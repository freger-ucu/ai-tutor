"""
EP7: Solver Prompts

Solves a single question with RAG-grounded explanation.
This is a teacher-facing endpoint - used for generating answer keys.

V2: Added support scoring and verification prompts (from agent.py patterns).
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


# =============================================================================
# V2 Prompts (from agent.py patterns)
# =============================================================================

SUPPORT_SCORING_PROMPT = """Оціни, наскільки добре кожен варіант відповіді підтверджується контекстом.

Питання: {stem}

Варіанти:
0) {option_0}
1) {option_1}
2) {option_2}
3) {option_3}

Контекст:
{context}

Для кожного варіанту вкажи оцінку підтримки від 0 до 10, де:
- 0 = контекст суперечить або не містить інформації
- 5 = часткове підтвердження
- 10 = пряме підтвердження з контексту

Формат відповіді (JSON):
{{"scores": {{"0": 0, "1": 0, "2": 0, "3": 0}}, "best": 0, "reasoning": "..."}}

Тільки JSON:"""


VERIFY_PROMPT = """Перевір, чи відповідь підтверджується контекстом.

Питання: {question}
Вибрана відповідь: {answer} ({answer_text})

Контекст:
{context}

Оціни:
1. Чи контекст містить пряме підтвердження відповіді?
2. Чи є суперечності?
3. Які терміни/факти могли б допомогти, але відсутні?

Формат відповіді (JSON):
{{"supported": true/false, "confidence": 0-10, "missing_terms": ["термін1", "термін2"], "reasoning": "..."}}

Тільки JSON:"""


# =============================================================================
# Original Solver Prompt
# =============================================================================

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
