"""
Question Validator Prompt

Validates generated test questions for correctness, topic relevance, and quality.
Used as part of the agentic test generation workflow.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


VALIDATOR_SYSTEM_PROMPT = """Ти — експерт з перевірки тестових завдань з математики та інших предметів.
Твоя роль — ретельно перевірити чи тестове питання коректне.

ВАЖЛИВО:
- Для математичних питань — обов'язково виконай обчислення самостійно
- Перевір чи позначена правильна відповідь справді правильна
- Перевір чи питання відповідає вказаній темі
- Відповідай ТІЛЬКИ у форматі JSON"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


def build_mc_validator_prompt(
    question: dict,
    topic_definition: str,
    subject: str,
    context: str = ""
) -> str:
    """
    Build prompt for validating a multiple choice question.

    The validator will:
    1. Solve the problem independently
    2. Compare with the marked correct answer
    3. Check topic relevance
    4. Return validation result as JSON
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    # Format options for display
    options_text = ""
    correct_letter = None
    for i, opt in enumerate(question.get("options", [])):
        letter = chr(65 + i)  # A, B, C, D
        options_text += f"{letter}) {opt}\n"
        if question.get("correct_answer", "").upper() == letter:
            correct_letter = letter

    prompt = f"""Перевір це тестове питання з предмету "{subject}".

## ТЕМА УРОКУ:
{topic_definition}

## ПИТАННЯ:
{question.get("question", "")}

## ВАРІАНТИ ВІДПОВІДЕЙ:
{options_text}
## ПОЗНАЧЕНА ПРАВИЛЬНА ВІДПОВІДЬ: {question.get("correct_answer", "?")}

## РІВЕНЬ СКЛАДНОСТІ: {question.get("difficulty", "medium")}

{f"## ПРАВИЛА ТА ФОРМУЛИ:{chr(10)}{subject_rules}" if subject_rules else ""}

{f"## КОНТЕКСТ З ПІДРУЧНИКА:{chr(10)}{context}" if context else ""}

## ТВОЄ ЗАВДАННЯ:

1. **РОЗВ'ЯЖИ** це питання самостійно, покроково
2. **ВИЗНАЧ** яка відповідь правильна (A, B, C або D)
3. **ПОРІВНЯЙ** з позначеною відповіддю
4. **ОЦІНИ** чи питання відповідає темі "{topic_definition}"

## ФОРМАТ ВІДПОВІДІ (тільки JSON):
{{
    "my_solution": "Короткий розв'язок...",
    "my_answer": "A",
    "marked_answer": "{question.get("correct_answer", "?")}",
    "answer_is_correct": true/false,
    "topic_relevance": 8,
    "issues": ["проблема 1", "проблема 2"],
    "is_valid": true/false
}}

КРИТЕРІЇ ВАЛІДНОСТІ:
- answer_is_correct = true (моя відповідь співпадає з позначеною)
- topic_relevance >= 7 (питання по темі)
- Немає критичних помилок у формулюванні

Надай ТІЛЬКИ JSON відповідь:"""

    return prompt


def build_open_validator_prompt(
    question: dict,
    topic_definition: str,
    subject: str,
    context: str = ""
) -> str:
    """
    Build prompt for validating an open question.

    The validator will:
    1. Check if question is clear and unambiguous
    2. Check if it has a definite, verifiable answer
    3. Check topic relevance
    4. Verify the explanation is correct
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    prompt = f"""Перевір це відкрите тестове питання з предмету "{subject}".

## ТЕМА УРОКУ:
{topic_definition}

## ПИТАННЯ:
{question.get("question", "")}

## ОЧІКУВАНА ВІДПОВІДЬ/ПОЯСНЕННЯ:
{question.get("explanation", "")}

## РІВЕНЬ СКЛАДНОСТІ: {question.get("difficulty", "medium")}

{f"## ПРАВИЛА ТА ФОРМУЛИ:{chr(10)}{subject_rules}" if subject_rules else ""}

{f"## КОНТЕКСТ З ПІДРУЧНИКА:{chr(10)}{context}" if context else ""}

## ТВОЄ ЗАВДАННЯ:

1. **ОЦІНИ** чи питання сформульовано чітко і однозначно
2. **ПЕРЕВІР** чи очікувана відповідь правильна
3. **ВИЗНАЧ** чи питання має одну конкретну відповідь (а не кілька можливих)
4. **ОЦІНИ** чи питання відповідає темі "{topic_definition}"
5. **ОЦІНИ** чи складність відповідає рівню "{question.get("difficulty", "medium")}"

## ФОРМАТ ВІДПОВІДІ (тільки JSON):
{{
    "is_clear": true/false,
    "has_definite_answer": true/false,
    "explanation_is_correct": true/false,
    "topic_relevance": 8,
    "difficulty_appropriate": true/false,
    "issues": ["проблема 1", "проблема 2"],
    "is_valid": true/false
}}

КРИТЕРІЇ ВАЛІДНОСТІ:
- is_clear = true (питання зрозуміле)
- has_definite_answer = true (є конкретна відповідь)
- explanation_is_correct = true (пояснення правильне)
- topic_relevance >= 7 (питання по темі)
- difficulty_appropriate = true (складність відповідна)

Надай ТІЛЬКИ JSON відповідь:"""

    return prompt


def build_validator_prompt(
    question: dict,
    topic_definition: str,
    subject: str,
    context: str = ""
) -> str:
    """
    Build appropriate validator prompt based on question type.

    Args:
        question: Question dict with 'type', 'question', 'options', etc.
        topic_definition: The topic the question should be about
        subject: Subject name (Алгебра, Українська мова, etc.)
        context: Optional RAG context for verification

    Returns:
        Formatted prompt string
    """
    q_type = question.get("type", "").lower()

    if q_type in ["multiple_choice", "single_choice"]:
        return build_mc_validator_prompt(question, topic_definition, subject, context)
    else:
        return build_open_validator_prompt(question, topic_definition, subject, context)
