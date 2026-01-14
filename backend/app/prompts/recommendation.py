"""
EP6: Student Recommendation Prompt

Generates a recommendation FOR THE TEACHER about a student's performance.
This is a teacher-facing endpoint - the output is read by the teacher, not the student.
"""

RECOMMENDATION_SYSTEM_PROMPT = """Ти — експерт з педагогічної аналітики.

Формат відповіді:
- Пиши українською мовою
- Лише факти та конкретні рекомендації
- БЕЗ привітань, звертань, прощань
- БЕЗ "Шановний вчителю", "Бажаю успіхів" тощо
- Стислий, діловий стиль
- Максимум 2-3 короткі абзаци"""


def build_recommendation_prompt(
    subject: str,
    average_grade: float,
    level: str,
    good_topics: list[str],
    bad_topics: list[str],
    missed_topics: list[str]
) -> str:
    """
    Build prompt for generating student recommendation FOR THE TEACHER.

    Args:
        subject: Subject name in Ukrainian
        average_grade: Student's average grade (0-12)
        level: Student level (weak/medium/strong)
        good_topics: Topics with score >= 10
        bad_topics: Topics with score < 6
        missed_topics: Topics from missed lessons

    Returns:
        Formatted prompt string for teacher consumption
    """
    level_ukrainian = {
        "weak": "слабкий",
        "medium": "середній",
        "strong": "сильний"
    }.get(level, level)

    # Format topics lists
    good_topics_text = ", ".join(good_topics[:5]) if good_topics else "немає даних"
    bad_topics_text = ", ".join(bad_topics[:5]) if bad_topics else "немає"
    missed_topics_text = ", ".join(missed_topics[:5]) if missed_topics else "немає"

    prompt = f"""Предмет: {subject}

Дані учня:
- Середній бал: {average_grade:.1f}/12
- Рівень: {level_ukrainian}
- Сильні теми (≥10): {good_topics_text}
- Слабкі теми (<6): {bad_topics_text}
- Пропуски: {missed_topics_text}

Надай стислу аналітику:
1. Сильні сторони учня
2. Проблемні зони (якщо є)
3. 2-3 конкретні поради для вчителя (індивідуальні заняття, додаткові матеріали, підходи до навчання)

Без вступу, без звертань, лише суть."""

    return prompt
