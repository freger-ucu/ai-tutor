"""
EP10: Test Feedback Prompt

Generates feedback after a student completes a test.
"""

FEEDBACK_SYSTEM_PROMPT = """Ти — досвідчений український педагог.
Твоя роль — надавати конструктивний зворотний зв'язок учням після виконання тесту.

Формат відповіді:
- Пиши українською мовою
- Будь підтримуючим і конструктивним
- Відзначай успіхи
- Вказуй на помилки без надмірної критики
- Давай конкретні поради для покращення
- Максимум 3-4 абзаци"""


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

    # Format incorrect topics
    if incorrect_by_topic:
        incorrect_topics_text = "\n".join([
            f"- {topic}: {len(questions)} помилок"
            for topic, questions in incorrect_by_topic.items()
        ])
    else:
        incorrect_topics_text = "Помилок немає!"

    # Format correct topics
    if correct_by_topic:
        correct_topics_text = "\n".join([
            f"- {topic}: {len(questions)} правильних"
            for topic, questions in correct_by_topic.items()
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

    prompt = f"""Склади зворотний зв'язок для учня після виконання тесту з предмету "{subject}".

Результат тесту:
- Правильних відповідей: {correct_count} з {total_count}
- Відсоток: {score_percent:.0f}%
- Загальна оцінка: {performance}

Правильні відповіді за темами/підтемами:
{correct_topics_text}

Помилки за темами/підтемами:
{incorrect_topics_text}

Напиши зворотний зв'язок для учня:
1. Оціни загальний результат
2. Відзнач сильні сторони (теми/підтеми з правильними відповідями)
3. Вкажи на теми/підтеми, де були помилки
4. Дай 2-3 конкретні поради для підготовки

Відповідь має бути мотивуючою та конструктивною."""

    return prompt
