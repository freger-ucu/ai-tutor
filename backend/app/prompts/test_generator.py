"""
EP4: Test Generator Prompt

Generates a pool of test questions based on a topic.
Uses chunked generation - one LLM call per difficulty level for reliability.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


TEST_GENERATOR_SYSTEM_PROMPT = """Ти — досвідчений український педагог-методист.
Твоя роль — створювати якісні тестові завдання для учнів 8-9 класів.

КРИТИЧНО ВАЖЛИВО:
- Всі питання мають бути СТРОГО по вказаній темі
- НЕ виходь за межі теми
- Пиши українською мовою
- Формулюй чітко та однозначно"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}

DIFFICULTY_DESCRIPTIONS = {
    "easy": {
        "name": "легкі",
        "description": "базові поняття, визначення, прості обчислення",
        "examples": "визначення термінів, прості формули, впізнавання понять"
    },
    "medium": {
        "name": "середні",
        "description": "застосування знань, типові задачі",
        "examples": "розв'язування стандартних задач, застосування формул"
    },
    "hard": {
        "name": "складні",
        "description": "аналіз, синтез, нестандартні задачі, комбінування понять",
        "examples": "задачі з кількома кроками, нестандартні умови, доведення"
    }
}


def build_chunked_test_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    difficulty: str,
    num_questions: int = 10,
) -> str:
    """
    Build prompt for generating questions of ONE difficulty level.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context
        difficulty: "easy", "medium", or "hard"
        num_questions: Number of questions to generate (default 10)

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")
    diff_info = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["medium"])

    prompt = f"""Створи {num_questions} тестових питань рівня "{diff_info['name'].upper()}" для учнів {grade} класу з предмету "{subject}".

## ТЕМА (всі питання ТІЛЬКИ по цій темі!):
{topic_definition}

## РІВЕНЬ СКЛАДНОСТІ: {diff_info['name'].upper()}
- {diff_info['description']}
- Приклади: {diff_info['examples']}

## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## ВИМОГИ:
- Рівно {num_questions} питань
- Всі питання рівня "{difficulty}"
- ~70% multiple_choice, ~30% open
- ВСІ питання СТРОГО по темі "{topic_definition}"

## ТИПИ ПИТАНЬ:
1. **multiple_choice** - 4 варіанти (A, B, C, D), одна правильна
2. **open** - відкрите питання

## JSON ФОРМАТ:
{{
    "questions": [
        {{
            "question": "Текст питання",
            "type": "multiple_choice",
            "difficulty": "{difficulty}",
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A",
            "explanation": "Коротке пояснення",
            "topic": "Підтема"
        }},
        {{
            "question": "Текст відкритого питання",
            "type": "open",
            "difficulty": "{difficulty}",
            "explanation": "Очікувана відповідь",
            "topic": "Підтема"
        }}
    ]
}}

Надай ТІЛЬКИ JSON, без додаткового тексту."""

    return prompt


# Keep old function for backwards compatibility but mark as deprecated
def build_test_generator_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    num_questions: int = 30,
) -> str:
    """
    DEPRECATED: Use build_chunked_test_prompt instead.
    This generates all questions in one call which is unreliable.
    """
    return build_chunked_test_prompt(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context,
        difficulty="medium",
        num_questions=num_questions
    )
