"""
EP4: Test Generator Prompt

Generates a pool of test questions based on a topic.
This is a teacher-facing endpoint - generates diverse questions for testing students.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


TEST_GENERATOR_SYSTEM_PROMPT = """Ти — досвідчений український педагог-методист.
Твоя роль — створювати якісні тестові завдання для учнів 8-9 класів.

Формат відповіді:
- Пиши українською мовою
- Створюй різноманітні питання (вибір, відкриті, задачі)
- Включай питання різної складності
- Формулюй чітко та однозначно
- Уникай двозначних відповідей"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


def build_test_generator_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    num_questions: int = 30,
) -> str:
    """
    Build prompt for generating a test pool.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context
        num_questions: Target number of questions (default 30)

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    # Calculate distribution by difficulty
    easy_count = num_questions // 3
    medium_count = num_questions // 3
    hard_count = num_questions - easy_count - medium_count

    prompt = f"""Створи набір тестових питань для учнів {grade} класу з предмету "{subject}".

## ТЕМА:
{topic_definition}

## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## ВИМОГИ ДО ПИТАНЬ:

### Кількість: {num_questions} питань
- Легкі (easy): ~{easy_count} питань - базові поняття, визначення
- Середні (medium): ~{medium_count} питань - застосування знань
- Складні (hard): ~{hard_count} питань - аналіз, синтез, нестандартні задачі

### Типи питань:
1. **multiple_choice** - 4 варіанти (A, B, C, D), одна правильна
2. **open** - відкрите питання, потребує розгорнутої відповіді

### Формат кожного питання:
{{
    "question": "Текст питання",
    "type": "multiple_choice" або "open",
    "difficulty": "easy" / "medium" / "hard",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],  // тільки для multiple_choice
    "correct_answer": "A" або "B" або "C" або "D",  // тільки для multiple_choice
    "explanation": "Коротке пояснення правильної відповіді",
    "topic": "Підтема цього питання"
}}

## ВАЖЛИВО:
- Для multiple_choice: завжди 4 варіанти, чітко вказуй правильну відповідь
- Для open: без варіантів і correct_answer
- explanation має бути коротким (1-2 речення)
- topic має відповідати конкретній підтемі з теми уроку

## ВІДПОВІДЬ:
Надай відповідь як JSON масив питань:
{{
    "title": "Тест: {topic_definition[:50]}",
    "questions": [
        // масив питань у форматі вище
    ]
}}"""

    return prompt
