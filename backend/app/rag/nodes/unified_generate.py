"""
Unified Generate Node - Subject-specific EXPERT prompts.

V3: Personalized agents through EXPERTISE, not examples.
Each subject has an expert persona with domain knowledge.

V4: Added self-consistency for Ukrainian language questions.
V5: Added concrete examples from agent.py for better accuracy.
V6: Added verify loop option (from solver V2 patterns) for answer verification.
"""

import logging
from typing import Dict, Any, List, Optional
from collections import Counter
import asyncio

from ..state import AgenticRAGState
from ..config import get_settings, get_subject_config
from ..utils.llm_client import generate_json_safe, get_llm_client
from ..utils.hybrid_retriever import get_retriever, format_context
from app.utils.json_parser import parse_json_response
# Import from shared prompts location (avoids circular import with solver.py)
from app.prompts.solver import VERIFY_PROMPT

logger = logging.getLogger(__name__)


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
Міркування: Односкладне називне має тільки підмет (іменник у називному). "Холодний день" — це воно.
Відповідь: B

---

Питання: Тире, тому що речення неповне, вжито в реченні:
Варіанти: A) Життя – це боротьба.  B) Боротись – значить жить.  C) Життя триває довго, щастя – мить.  D) І чебрець, і м'яту... – усе вирощувала мати.
Міркування: "щастя [триває] мить" — пропущене дієслово, тому тире.
Відповідь: C

---

Питання: Безсполучниковим складним є речення:
Варіанти: A) Я думаю, що він прав.  B) Сніг падав, вітер свистів.  C) Дощ йшов, але швидко припинився.  D) Той, хто прийшов першим, виграв.
Міркування: Безсполучникові - це складні речення без сполучників (і, та, але, що). B) 'Сніг падав, вітер свистів' - дві частини з'єднані тільки комою, без сполучників.
Відповідь: B

---

Питання: Немає додатка в такому реченні:
Варіанти: A) Посадила мати три ясени в полі.  B) Читати я навчився в п'ять років.  C) Мені годі думати про порятунок.  D) Довженко став відомим режисером.
Міркування: Додаток - другорядний член, що відповідає на питання непрямих відмінків (кого? чого? кому? чому? ким? чим?). D) 'режисером' - це іменна частина складеного присудка, а не додаток.
Відповідь: D

---

## ПИТАННЯ ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

ІНСТРУКЦІЯ:
1. Прочитай ДОВІДКОВИЙ МАТЕРІАЛ вище - він найбільш релевантний до питання
2. Знайди ПРАВИЛО в контексті
3. Проаналізуй КОЖЕН варіант окремо
4. Обери той що ТОЧНО відповідає правилу

JSON: {{"answer": 0-3, "rule": "правило з контексту", "analysis": "аналіз варіантів", "source": N}}"""


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

ІНСТРУКЦІЇ:
1. Уважно прочитай математичне питання і всі формули
2. Зверни увагу на LaTeX-нотацію: \\(x\\) — це змінна x, \\(\\frac{{a}}{{b}}\\) — це дріб a/b
3. Використай довідковий матеріал для перевірки формул та визначень
4. Покроково обмірковуй розв'язок і вибери правильну відповідь: 0, 1, 2 або 3

ПРИКЛАДИ:

Питання: Чому дорівнює знаменник геометричної прогресії \\((b_n)\\), якщо \\(b_1=56, b_2=7\\)?
Варіанти: 0) 8  1) 49  2) –8  3) \\(\\frac{{1}}{{8}}\\)
Міркування: Знаменник q = b₂/b₁ = 7/56 = 1/8
Відповідь: 3

---

Питання: Знайдіть множину розв'язків нерівності (x+6)²<0
Варіанти: 0) R  1) −6  2) 6  3) ∅
Міркування: Квадрат завжди ≥ 0, тому (x+6)² < 0 неможливо. Розв'язків немає (∅).
Відповідь: 3

---

Питання: Розв'яжіть рівняння 3x - 7 = 5
Варіанти: 0) 2  1) 4  2) -2/3  3) 12/3
Міркування: 3x - 7 = 5 → 3x = 12 → x = 4
Відповідь: 1

---

Питання: Область визначення функції f(x) = 1/(x-3)?
Варіанти: 0) x ≠ 3  1) x ≥ 3  2) x > 0  3) x ∈ R
Міркування: Знаменник не може дорівнювати нулю, тому x - 3 ≠ 0 → x ≠ 3
Відповідь: 0

---

## ЗАДАЧА ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Розв'яжи: формула → обчислення → відповідь.
JSON: {{"answer": 0-3, "solution": "розв'язання", "source": N}}"""


# =============================================================================
# HISTORY - Expert Prompt V5 (With Examples)
# =============================================================================

HISTORY_PROMPT = """Ти — досвідчений репетитор історії України для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ З ПІДРУЧНИКІВ:
{context}
---

ІНСТРУКЦІЇ:
1. Уважно прочитай питання про історичні події, дати, постаті
2. Звернися до довідкового матеріалу для перевірки дат, імен, подій
3. При порівнянні дат — шукай хронологічну послідовність
4. Вибери правильну відповідь: 0, 1, 2 або 3

ПРИКЛАДИ:

Питання: Яка подія відбулася найраніше?
Варіанти: 0) Корсунська битва  1) Пилявецька битва  2) Жовтоводська битва  3) Зборівська битва
Міркування: Хронологія: Жовтоводська (1648, квітень) → Корсунська (1648, травень) → Зборівська (1649).
Відповідь: 2

---

Питання: У якому році відбувся перший поділ Речі Посполитої?
Варіанти: 0) 1772 р.  1) 1775 р.  2) 1793 р.  3) 1795 р.
Міркування: Три поділи: 1772 (перший), 1793 (другий), 1795 (третій).
Відповідь: 0

---

## ПИТАННЯ (Історія України, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

Знайди в контексті факти, дати, події що стосуються питання.
Порівняй кожен варіант з інформацією в контексті.

JSON: {{"answer": 0-3, "fact": "факт з контексту", "analysis": "порівняння варіантів", "source": N}}"""


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

---

Знайди в контексті правило або факт для відповіді.
Проаналізуй кожен варіант.

JSON: {{"answer": 0-3, "rule": "правило з контексту", "analysis": "аналіз варіантів", "source": N}}"""


# =============================================================================
# SUBJECT-SPECIFIC PROMPT SELECTION
# =============================================================================

SUBJECT_PROMPTS = {
    "Українська мова": UKRAINIAN_EXPERT_PROMPT,
    "Алгебра": ALGEBRA_EXPERT_PROMPT,
    "Історія України": HISTORY_PROMPT,
}


def _format_options(answers: list) -> str:
    """Format answer options."""
    return "\n".join([f"{i}) {ans}" for i, ans in enumerate(answers)])


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
        Dict with: answer, agreement score, all responses, reasoning
    """
    # Generate multiple responses in parallel
    tasks = [
        generate_json_safe(
            prompt=prompt,
            temperature=temperature,
            default={"answer": 0, "analysis": "SC generation failed"}
        )
        for _ in range(num_samples)
    ]

    results = await asyncio.gather(*tasks)

    # Extract answers
    answers = []
    reasonings = []
    for r in results:
        ans = r.get("answer", r.get("answer_index", 0))
        if isinstance(ans, int) and 0 <= ans <= 3:
            answers.append(ans)
            reasonings.append(r.get("analysis", r.get("reasoning", "")))
        else:
            answers.append(0)
            reasonings.append("")

    # Majority vote
    if answers:
        counter = Counter(answers)
        most_common = counter.most_common(1)[0]
        final_answer = most_common[0]
        agreement = most_common[1] / len(answers)
    else:
        final_answer = 0
        agreement = 0.0

    # Get reasoning from the winning answer
    winning_idx = answers.index(final_answer) if final_answer in answers else 0
    winning_reasoning = reasonings[winning_idx] if winning_idx < len(reasonings) else ""

    return {
        "answer": final_answer,
        "agreement": agreement,
        "all_answers": answers,
        "reasoning": winning_reasoning,
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

    # Initial generation
    result = await generate_json_safe(
        prompt=prompt,
        temperature=0.0,
        default={"answer": 0, "analysis": "Generation failed", "source": 1}
    )
    llm_calls += 1

    answer_index = result.get("answer", result.get("answer_index", 0))
    reasoning = (
        result.get("analysis", "") or
        result.get("solution", "") or
        result.get("reason", "") or
        result.get("reasoning", "")
    )
    rule_found = result.get("rule", result.get("fact", ""))
    source_id = result.get("source", 1)

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
            result = await generate_json_safe(
                prompt=prompt,
                temperature=0.0,
                default={"answer": answer_index, "analysis": reasoning, "source": source_id}
            )
            llm_calls += 1

            answer_index = result.get("answer", result.get("answer_index", answer_index))
            reasoning = (
                result.get("analysis", reasoning) or
                result.get("solution", "") or
                result.get("reason", "") or
                result.get("reasoning", "")
            )
            rule_found = result.get("rule", result.get("fact", rule_found))

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
        # Standard single LLM call for other subjects
        result = await generate_json_safe(
            prompt=prompt,
            temperature=0.0,
            default={"answer": 0, "analysis": "Generation failed", "source": 1}
        )
        llm_calls += 1

        answer_index = result.get("answer", result.get("answer_index", 0))
        reasoning = (
            result.get("analysis", "") or
            result.get("solution", "") or
            result.get("reason", "") or
            result.get("reasoning", "")
        )
        rule_found = result.get("rule", result.get("fact", ""))
        source_id = result.get("source", 1)
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
