"""
EP6: Student Recommendation Prompt

Generates a recommendation FOR THE TEACHER about a student's performance.
This is a teacher-facing endpoint - the output is read by the teacher, not the student.
"""

RECOMMENDATION_SYSTEM_PROMPT = """Ти — експерт з педагогічної аналітики.

Формат відповіді:
- Українською мовою
- Максимально стисло, без води
- БЕЗ привітань, звертань, прощань
- Рівно 2 секції (див. нижче)"""


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
Середній бал: {average_grade:.1f}/12 | Рівень: {level_ukrainian}
Сильні теми (≥10): {good_topics_text}
Слабкі теми (<6): {bad_topics_text}
Пропуски: {missed_topics_text}

Дай відповідь у форматі:

**Аналіз**
2-3 речення: ключові факти про успішність.

**Рекомендації**
2-3 речення загалом: що робити вчителю. Без деталізації, без розкладу, без кількості вправ."""

    return prompt
