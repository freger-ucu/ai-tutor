"""
EP7: Solver Prompt

Solves a single question with RAG-grounded explanation.
This is a teacher-facing endpoint - used for generating answer keys.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


SOLVER_SYSTEM_PROMPT = """Ти — досвідчений український педагог-репетитор.
Твоя роль — розв'язувати завдання покроково з детальними поясненнями.

Формат відповіді:
- Пиши українською мовою
- Показуй всі кроки розв'язання
- Пояснюй логіку кожного кроку
- Посилайся на правила та формули з підручника
- Відповідь має бути зрозумілою для учня 8-9 класу"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


def build_solver_prompt(
    subject: str,
    grade: int,
    question: str,
    context: str,
) -> str:
    """
    Build prompt for solving a single question.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        question: Question text to solve
        context: Retrieved textbook context

    Returns:
        Formatted prompt string
    """
    # Get subject-specific rules
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    prompt = f"""Розв'яжи це завдання для учня {grade} класу з предмету "{subject}".

## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання та формули вище."}

## ЗАВДАННЯ:
{question}

## ІНСТРУКЦІЯ:
Розв'яжи завдання покроково:

1. **Аналіз задачі**: Що дано? Що потрібно знайти?
2. **Вибір методу**: Який підхід або формулу використати?
3. **Розв'язання**: Покрокове виконання з усіма обчисленнями
4. **Відповідь**: Чітка фінальна відповідь
5. **Перевірка** (якщо можливо): Підстановка результату назад

Пояснюй кожен крок так, щоб учень зрозумів логіку розв'язання.
Якщо є посилання на правила з підручника — вказуй їх."""

    return prompt
