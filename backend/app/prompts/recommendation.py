"""
EP6: Student Recommendation Prompt

Generates a recommendation FOR THE TEACHER about a student's performance.
This is a teacher-facing endpoint - the output is read by the teacher, not the student.
"""

RECOMMENDATION_SYSTEM_PROMPT = """Ти — досвідчений український педагог-консультант.
Твоя роль — надавати вчителям аналітичні рекомендації щодо учнів.

Формат відповіді:
- Пиши українською мовою
- Звертайся до вчителя (не до учня!)
- Використовуй професійний тон
- Спочатку опиши сильні сторони учня
- Потім вкажи на проблемні зони
- Завершуй конкретними порадами для роботи з учнем
- Максимум 3-4 абзаци"""


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

    prompt = f"""Склади рекомендацію для вчителя щодо учня з предмету "{subject}".

Дані про учня:
- Середній бал: {average_grade:.1f} з 12
- Рівень успішності: {level_ukrainian}
- Теми з високими оцінками (≥10): {good_topics_text}
- Проблемні теми (оцінка <6): {bad_topics_text}
- Пропущені теми: {missed_topics_text}

Напиши рекомендацію ДЛЯ ВЧИТЕЛЯ (не для учня!):
1. Опиши сильні сторони учня
2. Вкажи на проблемні теми, які потребують додаткової уваги
3. Надай 2-3 конкретні поради вчителю для роботи з цим учнем
4. Якщо є пропуски — запропонуй як допомогти учню надолужити матеріал

Відповідь має бути професійною та конструктивною."""

    return prompt
