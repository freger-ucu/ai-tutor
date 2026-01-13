"""
Unified Generate Node - Subject-specific EXPERT prompts.

V3: Personalized agents through EXPERTISE, not examples.
Each subject has an expert persona with domain knowledge.

V4: Added self-consistency for Ukrainian language questions.
"""

from typing import Dict, Any, List
from collections import Counter
import asyncio

from ..state import AgenticRAGState
from ..config import get_settings, get_subject_config
from ..utils.llm_client import generate_json_safe


# =============================================================================
# UKRAINIAN LANGUAGE - Expert Linguist Prompt V4 (Topic-Based)
# =============================================================================

UKRAINIAN_EXPERT_PROMPT = """Ти — експерт з української мови.

КЛЮЧОВІ ПРАВИЛА:
• Безособове речення: немає і НЕ МОЖЕ бути підмета (смеркає, холодно, блиснуло)
• Узагальнено-особове: дія для ВСІХ, 2 ос. одн. (не сховаєш, не кажи гоп)
• НЕ словосполучення: підмет+присудок, прийменник+іменник, фразеологізми, складена форма (найбільш + прикметник)
• Тире в неповному реченні: пропущено присудок (батько — на роботі)
• Сурядні сполучники: і, а, але, та, чи, або, однак
• Підрядні сполучники: бо, що, який, коли, якщо, щоб (НЕ сурядні!)
• Дієприслівниковий зворот: ЗАВЖДИ відокремлюється комами з ОБОХ боків
• Складений іменний присудок: "став режисером" - це присудок, НЕ додаток!

{context}

## ПИТАННЯ ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

ІНСТРУКЦІЯ:
1. Прочитай ТЕМИ вище - вони найбільш релевантні до питання
2. Знайди ПРАВИЛО в контексті
3. Проаналізуй КОЖЕН варіант окремо
4. Обери той що ТОЧНО відповідає правилу

JSON: {{"answer": 0-3, "rule": "правило з контексту", "analysis": "аналіз варіантів", "source": N}}"""


# =============================================================================
# ALGEBRA - Expert Mathematician Prompt
# =============================================================================

ALGEBRA_EXPERT_PROMPT = """Ти — експерт з математики.

ФОРМУЛИ:
• Геометрична прогресія: q = b₂/b₁
• Парабола: a>0 вгору, a<0 вниз
• x² ≥ 0 завжди, (x+a)² < 0 немає розв'язків

## КОНТЕКСТ:
{context}

## ЗАДАЧА ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Розв'яжи: формула → обчислення → відповідь.
JSON: {{"answer": 0-3, "solution": "розв'язання", "source": N}}"""


# =============================================================================
# HISTORY - Default RAG-focused Prompt (works well already)
# =============================================================================

HISTORY_PROMPT = """## КОНТЕКСТ З ПІДРУЧНИКА:
{context}

---

## ПИТАННЯ (Історія України, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

---

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
