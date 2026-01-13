"""
EP9: Open Question Evaluator Prompt

Evaluates student's answer to an open-ended question.
This is a student-facing endpoint - feedback should be constructive.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


EVALUATOR_SYSTEM_PROMPT = """Ти — досвідчений український педагог-репетитор.
Твоя роль — оцінювати відповіді учнів на відкриті питання.

Формат оцінювання:
- Будь справедливим, але доброзичливим
- Якщо відповідь правильна — похвали учня
- Якщо є помилки — вкажи на них конструктивно
- Поясни, як можна покращити відповідь
- Давай конкретні поради

Критерії правильності:
- Відповідь вважається ПРАВИЛЬНОЮ, якщо вона передає суть правильно
- Незначні помилки в формулюванні НЕ роблять відповідь неправильною
- Якщо відповідь частково правильна — оціни як НЕПРАВИЛЬНУ, але відзнач правильну частину"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


def build_evaluator_prompt(
    subject: str,
    grade: int,
    topic: str,
    subtopics: list[str],
    question: str,
    student_answer: str,
    context: str,
) -> str:
    """
    Build prompt for evaluating a student's open question answer.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic: Main topic of the question
        subtopics: Specific subtopics covered
        question: The question text
        student_answer: Student's answer to evaluate
        context: Retrieved textbook context

    Returns:
        Formatted prompt string
    """
    # Get subject-specific rules
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    subtopics_text = ", ".join(subtopics) if subtopics else "загальна тема"

    prompt = f"""Оціни відповідь учня {grade} класу з предмету "{subject}".

## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## ПИТАННЯ:
Тема: {topic}
Підтеми: {subtopics_text}

{question}

## ВІДПОВІДЬ УЧНЯ:
{student_answer if student_answer.strip() else "(учень не дав відповіді)"}

## ІНСТРУКЦІЯ:
Оціни відповідь учня за такими критеріями:

1. **Правильність**: Чи відповідь по суті правильна?
   - Якщо так — встанови correct: true
   - Якщо ні або частково — встанови correct: false

2. **Зворотний зв'язок**: Надай конструктивний відгук:
   - Якщо правильно: похвали + можливо, доповни
   - Якщо неправильно: вкажи на помилку + поясни правильну відповідь
   - Якщо пусто: підкажи, як підійти до питання

Відповідай українською мовою у форматі JSON:
{{
    "correct": true/false,
    "feedback": "твій зворотний зв'язок для учня"
}}"""

    return prompt
