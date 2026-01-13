"""
EP3: Notes Generator Prompts

Generates lesson notes adapted to student levels or individual needs.
This is a teacher-facing endpoint - notes should include teacher tips.
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


NOTES_SYSTEM_PROMPT = """Ти — досвідчений український педагог-методист.
Твоя роль — створювати якісні конспекти уроків для учнів 8-9 класів.

Формат відповіді:
- Пиши українською мовою
- Використовуй зрозумілу для учнів мову
- Структуруй матеріал логічно
- Включай приклади та пояснення
- Для вчителя: додавай нотатки про потенційні труднощі"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


LEVEL_DESCRIPTIONS = {
    "weak": {
        "name": "слабкий",
        "style": "Спрощений матеріал з детальними поясненнями. Більше прикладів, менше теорії. Базові вправи.",
        "focus": "Основні поняття без складних деталей. Покрокові інструкції."
    },
    "medium": {
        "name": "середній",
        "style": "Збалансований матеріал. Теорія + практика. Типові задачі з поясненнями.",
        "focus": "Стандартний рівень складності. Підготовка до контрольних робіт."
    },
    "strong": {
        "name": "сильний",
        "style": "Поглиблений матеріал. Складніші приклади. Олімпіадні завдання.",
        "focus": "Розширення знань за межі програми. Творчі та нестандартні задачі."
    },
}


def build_level_notes_prompt(
    subject: str,
    grade: int,
    level: str,
    topic_definition: str,
    context: str,
    gap_warnings: list[str] | None = None,
) -> str:
    """
    Build prompt for generating notes for a student level (EP3.1).

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        level: Student level (weak/medium/strong)
        topic_definition: Topic description
        context: Retrieved textbook context
        gap_warnings: List of topics students at this level struggle with

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")
    level_info = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["medium"])

    gap_section = ""
    if gap_warnings:
        gap_list = "\n".join(f"- {g}" for g in gap_warnings[:5])
        gap_section = f"""
## ПОПЕРЕДЖЕННЯ ПРО ПРОГАЛИНИ:
Учні цього рівня зазвичай мають труднощі з такими темами:
{gap_list}

Зверни увагу на ці теми при поясненні нового матеріалу!
"""

    prompt = f"""Створи конспект уроку для учнів {grade} класу з предмету "{subject}".

## ТЕМА УРОКУ:
{topic_definition}

## РІВЕНЬ УЧНІВ: {level_info['name'].upper()}
Стиль подачі: {level_info['style']}
Фокус: {level_info['focus']}
{gap_section}
## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## СТРУКТУРА КОНСПЕКТУ:

### TITLE:
Придумай коротку назву уроку (1 рядок)

### CONTENTS (для учнів):
1. **Вступ** - мотивація, чому це важливо
2. **Основна частина** - теорія з прикладами
3. **Практика** - 2-3 задачі з розв'язками
4. **Висновки** - ключові тезиси для запам'ятовування

### TEACHER_NOTES (для вчителя):
- На що звернути увагу
- Типові помилки учнів
- Додаткові приклади (якщо потрібно)
- Як перевірити розуміння

Відповідай у форматі JSON:
{{
    "title": "Назва уроку",
    "contents": "Повний текст конспекту в Markdown",
    "teacher_notes": "Нотатки для вчителя"
}}"""

    return prompt


def build_individual_notes_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    student_info: dict,
) -> str:
    """
    Build prompt for generating notes for a specific student (EP3.2).

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context
        student_info: Dict with student's level, problematic_topics, missed_topics

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    level = student_info.get("level", "medium")
    level_info = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["medium"])

    # Format student-specific info
    problematic_topics = student_info.get("problematic_topics", [])
    missed_topics = student_info.get("missed_topics", [])

    problems_text = ""
    if problematic_topics:
        problems_list = "\n".join(f"- {t}" for t in problematic_topics[:5])
        problems_text = f"""
## ПРОБЛЕМНІ ТЕМИ УЧНЯ:
{problems_list}
Зверни особливу увагу на ці теми при поясненні!
"""

    missed_text = ""
    if missed_topics:
        missed_list = "\n".join(f"- {t}" for t in missed_topics[:5])
        missed_text = f"""
## ПРОПУЩЕНІ ТЕМИ:
{missed_list}
Коротко нагадай ці теми, якщо вони пов'язані з новим матеріалом.
"""

    prompt = f"""Створи індивідуальний конспект уроку для учня {grade} класу з предмету "{subject}".

## ТЕМА УРОКУ:
{topic_definition}

## РІВЕНЬ УЧНЯ: {level_info['name'].upper()}
Стиль подачі: {level_info['style']}
{problems_text}{missed_text}
## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## СТРУКТУРА КОНСПЕКТУ:

### TITLE:
Придумай коротку назву (1 рядок)

### CONTENTS (адаптовано для цього учня):
1. **Повторення** - нагадай пов'язані теми (особливо пропущені)
2. **Новий матеріал** - з урахуванням рівня учня
3. **Практика** - задачі відповідної складності
4. **Самоперевірка** - як учень може перевірити себе

### TEACHER_NOTES:
- Рекомендації для роботи з цим учнем
- На що звернути увагу
- Як допомогти з проблемними темами

Відповідай у форматі JSON:
{{
    "title": "Назва уроку",
    "contents": "Повний текст конспекту в Markdown",
    "teacher_notes": "Нотатки для вчителя щодо цього учня"
}}"""

    return prompt
