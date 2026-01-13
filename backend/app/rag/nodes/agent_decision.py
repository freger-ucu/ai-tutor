"""
Agent Decision Node - Single LLM call for decision making.

This node combines multiple functions into ONE LLM call:
- Context quality assessment (replaces 8 grading calls)
- Question type classification (replaces analyze_question)
- Complexity estimation
- Decision routing: GENERATE or RETRY
"""

from typing import Dict, Any

from ..state import AgenticRAGState
from ..config import get_settings, get_subject_config, SUBJECT_CONFIGS
from ..utils.llm_client import generate_json_safe


def _get_type_options(subject: str) -> str:
    """Get question type options for subject."""
    config = SUBJECT_CONFIGS.get(subject)
    if config:
        return ", ".join(config.question_types)
    return "general"


def _format_context_summary(docs: list, max_docs: int = 4) -> str:
    """Format brief context summary for decision prompt."""
    if not docs:
        return "Контекст не знайдено."

    summaries = []
    for i, doc in enumerate(docs[:max_docs], 1):
        topic = doc.get("topic_title", "")
        score = doc.get("rrf_score", 0)
        # Just first 200 chars of content for quick assessment
        content_preview = doc.get("page_text", "")[:200].replace("\n", " ")
        summaries.append(f"{i}. [{topic}] (score: {score:.3f}): {content_preview}...")

    return "\n".join(summaries)


def _format_options(answers: list) -> str:
    """Format answer options."""
    return "\n".join([f"{i}) {ans}" for i, ans in enumerate(answers)])


AGENT_DECISION_PROMPT = """Ти AI-агент для освітньої системи. Оціни контекст та прийми рішення.

## ПИТАННЯ ({subject}, {grade} клас):
{question_text}

## ВАРІАНТИ ВІДПОВІДЕЙ:
{options}

## ЗНАЙДЕНИЙ КОНТЕКСТ (топ-{n_docs} документів):
{context_summary}

## ТВОЄ ЗАВДАННЯ:

1. **Оціни якість контексту** (0.0-1.0):
   - 0.8-1.0: Є ПРЯМА відповідь або правило
   - 0.5-0.7: Пов'язаний матеріал, можна вивести відповідь
   - 0.0-0.4: Нерелевантний або недостатній

2. **Класифікуй питання**:
   - Тип (один з): {type_options}
   - Складність: low (просте правило) | medium (кілька кроків) | high (аналіз, синтез)

3. **Прийми РІШЕННЯ**:
   - **GENERATE**: Контекст достатній для відповіді
   - **RETRY**: Контекст недостатній, потрібен інший пошук (вкажи retry_hint)

## ВІДПОВІДЬ (тільки JSON):
{{
    "context_quality": 0.0-1.0,
    "key_info_found": "що корисного є в контексті (коротко)" або null,
    "question_type": "тип",
    "complexity": "low|medium|high",
    "decision": "GENERATE|RETRY",
    "retry_hint": "підказка для пошуку (якщо RETRY)" або null
}}
"""


async def agent_decision_node(state: AgenticRAGState) -> Dict[str, Any]:
    """
    Agent decision node - single LLM call.

    Combines:
    - Context quality assessment
    - Question classification
    - Complexity estimation
    - Decision routing

    Updates state with:
    - agent_decision: "GENERATE" or "RETRY"
    - context_quality: Quality score 0-1
    - question_type: Subject-specific type
    - complexity: "low", "medium", or "high"
    - retry_hint: Hint for retry (if RETRY)
    - llm_calls_count: Incremented by 1

    Returns:
        State updates
    """
    subject = state["subject"]
    grade = state["grade"]
    question_text = state["question_text"]
    answers = state["answers"]
    docs = state.get("retrieved_docs", [])
    retry_count = state.get("retry_count", 0)
    llm_calls = state.get("llm_calls_count", 0)

    settings = get_settings()

    # Format prompt
    prompt = AGENT_DECISION_PROMPT.format(
        subject=subject,
        grade=grade,
        question_text=question_text,
        options=_format_options(answers),
        n_docs=len(docs),
        context_summary=_format_context_summary(docs),
        type_options=_get_type_options(subject),
    )

    # Single LLM call
    result = await generate_json_safe(
        prompt=prompt,
        temperature=0.0,
        default={
            "context_quality": 0.5,
            "question_type": "general",
            "complexity": "medium",
            "decision": "GENERATE",
            "retry_hint": None,
        }
    )

    # Extract values
    context_quality = result.get("context_quality", 0.5)
    decision = result.get("decision", "GENERATE")
    retry_hint = result.get("retry_hint")

    # Force GENERATE if:
    # 1. Already retried
    # 2. High context quality
    # 3. Retry limit reached
    if retry_count >= settings.max_retry_count:
        decision = "GENERATE"
    elif context_quality >= 0.7:
        decision = "GENERATE"

    # Force RETRY if context quality is very low and we haven't retried
    if context_quality < settings.min_context_quality and retry_count == 0:
        decision = "RETRY"
        if not retry_hint:
            retry_hint = f"правило для {result.get('question_type', 'питання')}"

    return {
        "agent_decision": decision,
        "context_quality": context_quality,
        "question_type": result.get("question_type", "general"),
        "complexity": result.get("complexity", "medium"),
        "retry_hint": retry_hint,
        "llm_calls_count": llm_calls + 1,
    }
