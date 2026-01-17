"""
EP10: Test Feedback Prompt

Generates feedback after a student completes a test.
"""

FEEDBACK_SYSTEM_PROMPT = """Ти — експерт з аналізу навчальних результатів.

Формат відповіді:
- Українською мовою
- Дуже коротко і по суті
- БЕЗ привітань, звертань, прощань
- Рівно 3 секції (див. нижче)"""


def build_feedback_prompt(
    subject: str,
    correct_count: int,
    total_count: int,
    incorrect_by_topic: dict[str, list[str]],
    correct_by_topic: dict[str, list[str]] | None = None
) -> str:
    """
    Build prompt for generating test feedback.

    Args:
        subject: Subject name in Ukrainian
        correct_count: Number of correct answers
        total_count: Total number of questions
        incorrect_by_topic: Dict mapping topic -> list of incorrect questions
        correct_by_topic: Dict mapping topic -> list of correct questions

    Returns:
        Formatted prompt string
    """
    score_percent = (correct_count / total_count * 100) if total_count > 0 else 0

    # Format incorrect topics (list each focus)
    if incorrect_by_topic:
        incorrect_topics_text = "\n".join([
            f"- {focus}" for focus in incorrect_by_topic.keys()
        ])
    else:
        incorrect_topics_text = "Помилок немає!"

    # Format correct topics (list each focus)
    if correct_by_topic:
        correct_topics_text = "\n".join([
            f"- {focus}" for focus in correct_by_topic.keys()
        ])
    else:
        correct_topics_text = "Немає правильних відповідей"

    # Determine performance level
    if score_percent >= 90:
        performance = "відмінний результат"
    elif score_percent >= 70:
        performance = "добрий результат"
    elif score_percent >= 50:
        performance = "задовільний результат"
    else:
        performance = "потребує покращення"

    prompt = f"""Предмет: {subject}
Результат: {correct_count}/{total_count} ({score_percent:.0f}%) — {performance}

Успішні теми:
{correct_topics_text}

Проблемні теми:
{incorrect_topics_text}

Дай відповідь у форматі:

**Результат**
1 коротке речення: оцінка {score_percent:.0f}% і загальний висновок.

**Аналіз**
2 речення: що вдалося + де прогалини (в одному блоці).

**Рекомендації**
1-2 речення: конкретна порада що робити далі."""

    return prompt
