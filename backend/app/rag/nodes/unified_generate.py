"""
Unified Generate Node - Subject-specific EXPERT prompts.

V3: Personalized agents through EXPERTISE, not examples.
Each subject has an expert persona with domain knowledge.

V4: Added self-consistency for Ukrainian language questions.
V5: Added concrete examples from agent.py for better accuracy.
V6: Added verify loop option (from solver V2 patterns) for answer verification.
V7: Added structured outputs with Pydantic schemas for guaranteed valid JSON.
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from collections import Counter
import asyncio

from pydantic import BaseModel, Field

from ..state import AgenticRAGState
from ..config import get_settings, get_subject_config
from ..utils.llm_client import generate_structured_safe, get_llm_client
from ..utils.hybrid_retriever import get_retriever, format_context
from app.utils.json_parser import parse_json_response
# Import from shared prompts location (avoids circular import with solver.py)
from app.prompts.solver import VERIFY_PROMPT

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC RESPONSE SCHEMA FOR STRUCTURED OUTPUTS
# =============================================================================

class AnswerResponse(BaseModel):
    """Simple answer schema with letter A-D."""
    answer: Literal["A", "B", "C", "D"] = Field(description="Answer: A, B, C or D")


def _letter_to_index(letter: str) -> int:
    """Convert A/B/C/D to 0/1/2/3."""
    return {"A": 0, "B": 1, "C": 2, "D": 3}.get(str(letter).upper(), 0)


# =============================================================================
# UKRAINIAN LANGUAGE - Expert Linguist Prompt V5 (With Examples)
# =============================================================================

UKRAINIAN_EXPERT_PROMPT = """Ти — досвідчений репетитор української мови для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

КЛЮЧОВІ ПРАВИЛА:
• Безособове речення: немає і НЕ МОЖЕ бути підмета (смеркає, холодно, блиснуло)
• Узагальнено-особове: дія для ВСІХ, 2 ос. одн. (не сховаєш, не кажи гоп)
• НЕ словосполучення: підмет+присудок, прийменник+іменник, фразеологізми, складена форма (найбільш + прикметник)
• Тире в неповному реченні: пропущено присудок (батько — на роботі)
• Сурядні сполучники: і, а, але, та, чи, або, однак
• Підрядні сполучники: бо, що, який, коли, якщо, щоб (НЕ сурядні!)
• Дієприслівниковий зворот: ЗАВЖДИ відокремлюється комами з ОБОХ боків
• Складений іменний присудок: "став режисером" - це присудок, НЕ додаток!

ПРИКЛАДИ:

Питання: Односкладним називним є речення
Варіанти: A) Теплий вітерець повіяв.  B) Холодний день.  C) Камінь холодний  D) Сьогодні холодний день.
Відповідь: B

Питання: Тире, тому що речення неповне, вжито в реченні:
Варіанти: A) Життя – це боротьба.  B) Боротись – значить жить.  C) Життя триває довго, щастя – мить.  D) І чебрець, і м'яту... – усе вирощувала мати.
Відповідь: C

Питання: Безсполучниковим складним є речення:
Варіанти: A) Я думаю, що він прав.  B) Сніг падав, вітер свистів.  C) Дощ йшов, але швидко припинився.  D) Той, хто прийшов першим, виграв.
Відповідь: B

Питання: Немає додатка в такому реченні:
Варіанти: A) Посадила мати три ясени в полі.  B) Читати я навчився в п'ять років.  C) Мені годі думати про порятунок.  D) Довженко став відомим режисером.
Відповідь: D

---

## ПИТАННЯ ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Відповідай ТІЛЬКИ буквою: A, B, C або D."""


# =============================================================================
# ALGEBRA - Expert Mathematician Prompt V5 (With Examples)
# =============================================================================

ALGEBRA_EXPERT_PROMPT = """Ти — досвідчений репетитор з математики для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

ФОРМУЛИ:
• Геометрична прогресія: q = b₂/b₁
• Парабола: a>0 вгору, a<0 вниз
• x² ≥ 0 завжди, (x+a)² < 0 немає розв'язків

ПРИКЛАДИ:

Питання: Чому дорівнює знаменник геометричної прогресії (b_n), якщо b_1=56, b_2=7?
Варіанти: A) 8  B) 49  C) –8  D) 1/8
Відповідь: D

Питання: Знайдіть множину розв'язків нерівності (x+6)²<0
Варіанти: A) R  B) −6  C) 6  D) ∅
Відповідь: D

Питання: Розв'яжіть рівняння 3x - 7 = 5
Варіанти: A) 2  B) 4  C) -2/3  D) 12/3
Відповідь: B

Питання: Область визначення функції f(x) = 1/(x-3)?
Варіанти: A) x ≠ 3  B) x ≥ 3  C) x > 0  D) x ∈ R
Відповідь: A

---

## ЗАДАЧА ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Відповідай ТІЛЬКИ буквою: A, B, C або D."""


# =============================================================================
# HISTORY - Expert Prompt V5 (With Examples)
# =============================================================================

HISTORY_PROMPT = """Ти — досвідчений репетитор історії України для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ З ПІДРУЧНИКІВ:
{context}
---

ПРИКЛАДИ:

Питання: Яка подія відбулася найраніше?
Варіанти: A) Корсунська битва  B) Пилявецька битва  C) Жовтоводська битва  D) Зборівська битва
Відповідь: C

Питання: У якому році відбувся перший поділ Речі Посполитої?
Варіанти: A) 1772 р.  B) 1775 р.  C) 1793 р.  D) 1795 р.
Відповідь: A

---

## ПИТАННЯ (Історія України, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

Відповідай ТІЛЬКИ буквою: A, B, C або D."""


# =============================================================================
# DEFAULT PROMPT - For other subjects
# =============================================================================

DEFAULT_PROMPT = """## КОНТЕКСТ З ПІДРУЧНИКА:
{context}

---

## ПИТАННЯ ({subject}, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

Відповідай ТІЛЬКИ буквою: A, B, C або D."""


# =============================================================================
# SUBJECT-SPECIFIC PROMPT SELECTION
# =============================================================================

SUBJECT_PROMPTS = {
    "Українська мова": UKRAINIAN_EXPERT_PROMPT,
    "Алгебра": ALGEBRA_EXPERT_PROMPT,
    "Історія України": HISTORY_PROMPT,
}


def _format_options(answers: list) -> str:
    """Format answer options with letters A-D."""
    letters = ["A", "B", "C", "D"]
    return "\n".join([f"{letters[i]}) {ans}" for i, ans in enumerate(answers[:4])])


def _get_prompt_for_subject(subject: str) -> str:
    """Get the appropriate expert prompt for a subject."""
    return SUBJECT_PROMPTS.get(subject, DEFAULT_PROMPT)


async def _run_self_consistency(
    prompt: str,
    num_samples: int = 3,
    temperature: float = 0.3,
) -> Dict[str, Any]:
    """
    Run self-consistency: generate multiple samples and take majority vote.

    Returns:
        Dict with: answer (index 0-3), agreement score, all responses, reasoning
    """
    # Generate multiple responses in parallel
    tasks = [
        generate_structured_safe(
            prompt=prompt,
            response_schema=AnswerResponse,
            temperature=temperature,
            default={"answer": "A"}
        )
        for _ in range(num_samples)
    ]

    results = await asyncio.gather(*tasks)

    # Extract answers (convert letters to indices)
    answers = []
    for r in results:
        letter = r.get("answer", "A")
        idx = _letter_to_index(letter)
        answers.append(idx)

    # Majority vote
    if answers:
        counter = Counter(answers)
        most_common = counter.most_common(1)[0]
        final_answer = most_common[0]
        agreement = most_common[1] / len(answers)
    else:
        final_answer = 0
        agreement = 0.0

    return {
        "answer": final_answer,
        "agreement": agreement,
        "all_answers": answers,
        "reasoning": "",
        "all_results": results,
    }


# =============================================================================
# V6: Verify Loop Functions (from solver V2 patterns)
# =============================================================================


def _parse_verification(response: str) -> Dict[str, Any]:
    """Parse verification response from LLM."""
    try:
        data = parse_json_response(response, {}, "Verification")
        return {
            "supported": data.get("supported", True),
            "confidence": data.get("confidence", 5),
            "missing_terms": data.get("missing_terms", []),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.warning(f"Failed to parse verification: {e}")
        return {"supported": True, "confidence": 5, "missing_terms": [], "reasoning": ""}


async def _verify_answer(
    question: str,
    answer_index: int,
    answer_text: str,
    context: str,
) -> Dict[str, Any]:
    """
    Verify if the selected answer is well-supported by context.

    Returns:
        Dict with: supported (bool), confidence (0-10), missing_terms (list), reasoning (str)
    """
    if not context or len(context) < 100:
        return {"supported": False, "confidence": 0, "missing_terms": [], "reasoning": "No context"}

    prompt = VERIFY_PROMPT.format(
        question=question,
        answer=answer_index,
        answer_text=answer_text,
        context=context[:4000],
    )

    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        temperature=0.0,
        max_tokens=300,
    )

    return _parse_verification(response)


async def _refine_retrieval(
    stem: str,
    missing_terms: List[str],
    subject: str,
    grade: int,
) -> str:
    """
    Refine retrieval with missing terms identified during verification.

    Returns:
        Additional context from refined retrieval
    """
    if not missing_terms:
        return ""

    refined_query = f"{stem} {' '.join(missing_terms)}"
    logger.info(f"Refining retrieval with: {refined_query[:100]}...")

    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=refined_query,
        subject=subject,
        grade=grade,
        top_k=3,
    )

    context, _ = format_context(docs, max_chars=3000, subject=subject)
    return context


async def generate_answer_with_verify(
    state: AgenticRAGState,
    max_iterations: int = 2,
) -> Dict[str, Any]:
    """
    Generate answer with optional verify-refine loop.

    V6 Feature: Verifies the answer is supported by context and
    refines retrieval if needed (up to max_iterations).

    Args:
        state: The RAG state with question and context
        max_iterations: Max verify-refine iterations (default 2)

    Returns:
        State updates with final answer, confidence, and verification info
    """
    subject = state["subject"]
    grade = state["grade"]
    question_text = state["question_text"]
    answers = state["answers"]
    context_text = state.get("context_text", "")
    references = state.get("references", [])
    llm_calls = state.get("llm_calls_count", 0)

    # Get subject-specific expert prompt
    prompt_template = _get_prompt_for_subject(subject)

    # Build initial prompt
    prompt = prompt_template.format(
        context=context_text if context_text else "Контекст не знайдено.",
        subject=subject,
        grade=grade,
        question=question_text,
        options=_format_options(answers),
    )

    # Initial generation with letter-based schema
    result = await generate_structured_safe(
        prompt=prompt,
        response_schema=AnswerResponse,
        temperature=0.0,
        default={"answer": "A"}
    )
    llm_calls += 1

    answer_letter = result.get("answer", "A")
    answer_index = _letter_to_index(answer_letter)
    reasoning = ""
    rule_found = ""
    source_id = 1

    # Validate answer_index
    if not isinstance(answer_index, int) or answer_index < 0 or answer_index >= len(answers):
        answer_index = 0

    # Verify loop
    verification = None
    current_context = context_text

    for iteration in range(max_iterations):
        answer_text = answers[answer_index] if answer_index < len(answers) else ""

        verification = await _verify_answer(
            question=question_text,
            answer_index=answer_index,
            answer_text=answer_text,
            context=current_context,
        )
        llm_calls += 1

        logger.info(
            f"Verification iter {iteration + 1}: supported={verification['supported']}, "
            f"confidence={verification['confidence']}, missing={verification.get('missing_terms', [])}"
        )

        # If answer is well-supported or we have no missing terms, we're done
        if verification["supported"] and verification["confidence"] >= 7:
            break

        if not verification.get("missing_terms"):
            break

        # Refine retrieval and regenerate
        refined_context = await _refine_retrieval(
            stem=question_text,
            missing_terms=verification["missing_terms"],
            subject=subject,
            grade=grade,
        )

        if refined_context:
            # Merge contexts
            current_context = f"{current_context}\n\n{refined_context}"

            # Rebuild prompt with refined context
            prompt = prompt_template.format(
                context=current_context,
                subject=subject,
                grade=grade,
                question=question_text,
                options=_format_options(answers),
            )

            # Regenerate answer
            result = await generate_structured_safe(
                prompt=prompt,
                response_schema=AnswerResponse,
                temperature=0.0,
                default={"answer": "A"}
            )
            llm_calls += 1

            answer_letter = result.get("answer", "A")
            answer_index = _letter_to_index(answer_letter)

            # Validate answer_index
            if not isinstance(answer_index, int) or answer_index < 0 or answer_index >= len(answers):
                answer_index = 0

    # Validate source_id
    if not isinstance(source_id, int) or source_id < 1:
        source_id = 1

    # Get source reference details
    source_ref = {}
    if references and 0 < source_id <= len(references):
        source_ref = references[source_id - 1]

    # Calculate confidence from verification
    final_confidence = 0.8
    if verification:
        v_confidence = verification.get("confidence", 5) / 10.0
        final_confidence = (0.8 + v_confidence) / 2

    # Build rich reasoning with source and verification info
    full_reasoning = reasoning
    if rule_found:
        full_reasoning = f"Правило: {rule_found}. {reasoning}"
    if source_ref:
        full_reasoning += f" [Джерело: {source_ref.get('topic', '')}, стор. {source_ref.get('page', '')}]"
    if verification:
        full_reasoning += f" [Verify: supported={verification['supported']}, confidence={verification['confidence']}/10]"

    return {
        "initial_answer": {"answer": answer_index, "reasoning": reasoning},
        "final_answer_index": answer_index,
        "final_confidence": final_confidence,
        "final_reasoning": full_reasoning,
        "rule_found": rule_found,
        "source_reference": source_ref,
        "used_self_consistency": False,
        "sc_agreement": 0.0,
        "verification": verification,
        "llm_calls_count": llm_calls,
    }


async def generate_answer_node(state: AgenticRAGState) -> Dict[str, Any]:
    """
    Generate answer using subject-specific EXPERT prompts.

    V4 Changes:
    - Self-consistency for Ukrainian language (3 samples, majority vote)
    - Expert persona for each subject (linguist, mathematician)
    - Domain knowledge embedded in prompt

    V7 Changes:
    - Uses structured outputs (json_schema) for guaranteed valid JSON
    - Pydantic schemas per subject ensure correct response format

    Returns:
        State updates with final answer and source reference
    """
    subject = state["subject"]
    grade = state["grade"]
    question_text = state["question_text"]
    answers = state["answers"]
    context_text = state.get("context_text", "")
    references = state.get("references", [])
    llm_calls = state.get("llm_calls_count", 0)

    # Get subject-specific expert prompt
    prompt_template = _get_prompt_for_subject(subject)

    # Build prompt
    prompt = prompt_template.format(
        context=context_text if context_text else "Контекст не знайдено.",
        subject=subject,
        grade=grade,
        question=question_text,
        options=_format_options(answers),
    )

    # Self-consistency disabled - doesn't help when model consistently wrong
    # use_sc = subject == "Українська мова"
    use_sc = False  # Disabled: SC gives 100% agreement on wrong answers

    if use_sc:
        # Self-consistency: 3 samples with temperature=0.3, majority vote
        sc_result = await _run_self_consistency(
            prompt=prompt,
            num_samples=3,
            temperature=0.3,
        )
        llm_calls += 3

        answer_index = sc_result["answer"]
        reasoning = sc_result["reasoning"]
        sc_agreement = sc_result["agreement"]
        all_answers = sc_result["all_answers"]

        # Get rule from first result that has it
        rule_found = ""
        source_id = 1
        for r in sc_result["all_results"]:
            if r.get("rule"):
                rule_found = r["rule"]
            if r.get("source"):
                source_id = r["source"]
                break
    else:
        # V8: Use letter-based schema (A/B/C/D) for clarity
        result = await generate_structured_safe(
            prompt=prompt,
            response_schema=AnswerResponse,
            temperature=0.0,
            default={"answer": "A"}
        )
        llm_calls += 1

        answer_letter = result.get("answer", "A")
        answer_index = _letter_to_index(answer_letter)
        reasoning = ""
        rule_found = ""
        source_id = 1
        sc_agreement = 0.0
        all_answers = []

    # Validate answer_index
    if not isinstance(answer_index, int) or answer_index < 0 or answer_index > 3:
        answer_index = 0

    # Validate source_id
    if not isinstance(source_id, int) or source_id < 1:
        source_id = 1

    # Get source reference details
    source_ref = {}
    if references and 0 < source_id <= len(references):
        source_ref = references[source_id - 1]

    # Build rich reasoning with source
    full_reasoning = reasoning
    if rule_found:
        full_reasoning = f"Правило: {rule_found}. {reasoning}"
    if source_ref:
        full_reasoning += f" [Джерело: {source_ref.get('topic', '')}, стор. {source_ref.get('page', '')}]"
    if use_sc:
        full_reasoning += f" [SC: {all_answers}, agreement: {sc_agreement:.0%}]"

    return {
        "initial_answer": {"answer": answer_index, "reasoning": reasoning},
        "final_answer_index": answer_index,
        "final_confidence": sc_agreement if use_sc else 0.8,
        "final_reasoning": full_reasoning,
        "rule_found": rule_found,
        "source_reference": source_ref,
        "used_self_consistency": use_sc,
        "sc_agreement": sc_agreement,
        "llm_calls_count": llm_calls,
    }


# Alias for backward compatibility
unified_generate_node = generate_answer_node
