"""
EP3: Notes Generator Prompts

Generates lesson notes adapted to student levels or individual needs.
This is a teacher-facing endpoint - notes should include teacher tips.

Both EP3.1 (by level) and EP3.2 (by student list) converge to use
aggregated statistics from aggregate_student_gaps().
"""

from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


NOTES_SYSTEM_PROMPT = """Ти — досвідчений український педагог-методист.
Твоя роль — створювати навчальні матеріали для учнів 8-9 класів.

ВАЖЛИВО про структуру відповіді:
- CONTENTS: пиши БЕЗПОСЕРЕДНЬО для учнів, як підручник або конспект для самостійного читання
- TEACHER_NOTES: окремо для вчителя - рекомендації, на що звернути увагу

СТИЛЬ НАПИСАННЯ:
- Пиши діловим, інформативним стилем — одразу до суті
- НЕ використовуй привітання ("Привіт!", "Друзі!", "Сьогодні ми...")
- НЕ використовуй емоційні вигуки чи розмовний стиль
- Пиши як якісний підручник: чітко, структуровано, по факту

Формат:
- Пиши українською мовою
- Використовуй зрозумілу для учнів мову
- Структуруй матеріал логічно
- Включай приклади та пояснення"""


SUBJECT_RULES_MAP = {
    "Алгебра": ALGEBRA_RULES,
    "Українська мова": UKRAINIAN_RULES,
    "Історія України": HISTORY_RULES,
}


LEVEL_DESCRIPTIONS = {
    "weak": {
        "name": "слабкий",
        "style": """СПРОЩЕНИЙ матеріал:
- Прості речення, базова термінологія
- Багато покрокових прикладів з детальними поясненнями кожного кроку
- Тільки найважливіші формули (1-2)
- Легкі задачі з однією дією""",
        "focus": "Мета: учень зрозумів ОСНОВИ. Без складних випадків та винятків."
    },
    "medium": {
        "name": "середній",
        "style": """СТАНДАРТНИЙ матеріал:
- Повна теорія з прикладами
- Типові задачі середньої складності
- Основні формули та правила
- Підготовка до контрольних робіт""",
        "focus": "Мета: учень засвоїв тему на рівні шкільної програми."
    },
    "strong": {
        "name": "сильний",
        "style": """ПОГЛИБЛЕНИЙ матеріал:
- Розширена теорія, додаткові факти
- Складні та нестандартні задачі
- Олімпіадні завдання
- Зв'язки з іншими темами""",
        "focus": "Мета: учень готовий до олімпіад та поглибленого вивчення."
    },
}


def format_aggregated_gaps(
    aggregated_gaps: dict,
    total_students: int | None = None
) -> str:
    """
    Format aggregated gap statistics into a readable section for the prompt.

    Args:
        aggregated_gaps: Dict from aggregate_student_gaps() with:
            - weak_topics: Dict[topic, {count, avg_score, student_ids}]
            - skipped_topics: Dict[topic, {count, student_ids}]
            - total_students: int
        total_students: Override for total (optional)

    Returns:
        Formatted string section for prompt
    """
    raw_weak = aggregated_gaps.get("weak_topics", {})
    raw_skipped = aggregated_gaps.get("skipped_topics", {})
    total = total_students or aggregated_gaps.get("total_students", 0)

    # Clean topic names (strip whitespace/newlines) and filter empty
    weak_topics = {
        topic.strip(): info
        for topic, info in raw_weak.items()
        if topic.strip()
    }
    skipped_topics = {
        topic.strip(): info
        for topic, info in raw_skipped.items()
        if topic.strip()
    }

    if not weak_topics and not skipped_topics:
        return ""

    lines = ["## ДАНІ ПРО УЧНІВ:"]
    lines.append(f"Кількість учнів у вибірці: {total}")
    lines.append("")

    # Weak topics section
    if weak_topics:
        lines.append("### Теми з низькими оцінками (середній бал < 6):")
        # Sort by count descending
        sorted_weak = sorted(
            weak_topics.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        for topic, info in sorted_weak[:10]:  # Top 10
            count = info["count"]
            avg = info.get("avg_score", 0)
            pct = round(count / total * 100) if total > 0 else 0
            lines.append(f"- **{topic}**: {count} учнів ({pct}%), середній бал: {avg}")
        lines.append("")

    # Skipped topics section
    if skipped_topics:
        lines.append("### Пропущені теми (уроки):")
        # Sort by count descending
        sorted_skipped = sorted(
            skipped_topics.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        for topic, info in sorted_skipped[:10]:  # Top 10
            count = info["count"]
            pct = round(count / total * 100) if total > 0 else 0
            lines.append(f"- **{topic}**: пропущено {count} учнями ({pct}%)")
        lines.append("")

    # Summary for teacher
    lines.append("### Підсумок:")

    if weak_topics:
        top_weak = list(weak_topics.keys())[:3]
        lines.append(f"- Низькі оцінки з: {', '.join(top_weak)}")

    if skipped_topics:
        top_skipped = list(skipped_topics.keys())[:3]
        lines.append(f"- Пропущені уроки: {', '.join(top_skipped)}")

    lines.append("")
    return "\n".join(lines)


def build_level_notes_prompt(
    subject: str,
    grade: int,
    level: str,
    topic_definition: str,
    context: str,
    gap_warnings: list[str] | None = None,
    aggregated_gaps: dict | None = None,
    missed_prereqs: list[str] | None = None,
) -> str:
    """
    Build prompt for generating notes for a student level (EP3.1).

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        level: Student level (weak/medium/strong)
        topic_definition: Topic description
        context: Retrieved textbook context (may include prereq context section)
        gap_warnings: (deprecated) List of topics - use aggregated_gaps instead
        aggregated_gaps: Dict from aggregate_student_gaps() with detailed statistics
        missed_prereqs: List of prerequisite topics that students missed/struggled with

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")
    level_info = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["medium"])

    # Use new aggregated gaps format if available, fall back to old format
    gap_section = ""
    if aggregated_gaps:
        gap_section = format_aggregated_gaps(aggregated_gaps)
    elif gap_warnings:
        # Backwards compatibility with old format
        gap_list = "\n".join(f"- {g}" for g in gap_warnings[:5])
        gap_section = f"""
## ПОПЕРЕДЖЕННЯ ПРО ПРОГАЛИНИ:
Учні цього рівня зазвичай мають труднощі з такими темами:
{gap_list}

Зверни увагу на ці теми при поясненні нового матеріалу!
"""

    # Build structure instructions based on whether there are missed prereqs
    has_recap = missed_prereqs and len(missed_prereqs) > 0
    prereq_list = ", ".join(missed_prereqs) if missed_prereqs else ""

    if has_recap:
        structure_instructions = f"""Структура (ОБОВ'ЯЗКОВО дотримуйся!):
1. **## Повторення** - коротке нагадування пропущених/слабких пререквізитів: {prereq_list}
   - Стисло поясни ключові поняття з цих тем
   - Дай 1-2 приклади для кожного пререквізиту
2. **## Урок** - основний матеріал нової теми
   - Теорія: означення, формули, правила
   - Приклади: задачі з розв'язками
   - Підсумок: ключові формули

ВАЖЛИВО: Секція "## Повторення" ОБОВ'ЯЗКОВА, бо учні мають прогалини у пререквізитах!"""
        teacher_recap_note = f"""
ВАЖЛИВО: Учні мають прогалини у пререквізитах ({prereq_list}).
РЕКОМЕНДАЦІЯ: Почніть урок з повторення цих тем. Переконайтесь, що учні розуміють базові поняття перед переходом до нового матеріалу."""
    else:
        structure_instructions = """Структура:
1. **## Урок** - основний матеріал теми
   - Теорія: означення, формули, правила (складність відповідно до рівня!)
   - Приклади: задачі з розв'язками (складність відповідно до рівня!)
   - Підсумок: ключові формули"""
        teacher_recap_note = ""

    prompt = f"""Створи навчальний матеріал для учнів {grade} класу з предмету "{subject}".

## ТЕМА:
{topic_definition}

## РІВЕНЬ УЧНІВ: {level_info['name'].upper()}
Стиль подачі: {level_info['style']}
Фокус: {level_info['focus']}

{gap_section}
## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## СТРУКТУРА ВІДПОВІДІ:

### TITLE:
Коротка назва теми (1 рядок)

### CONTENTS (навчальний матеріал ДЛЯ УЧНІВ):
КРИТИЧНО ВАЖЛИВО — АДАПТУЙ ДО РІВНЯ "{level_info['name'].upper()}"!
{level_info['style']}
{level_info['focus']}

Формат:
- НЕ пиши "Привіт!", "Друзі!", "Сьогодні ми вивчимо..."
- Починай одразу з матеріалу

{structure_instructions}

### TEACHER_NOTES (нотатки ДЛЯ ВЧИТЕЛЯ):
Коротка характеристика (МАКСИМУМ 10 рядків) у вигляді списку:
1. Рівень учнів (1-2 речення)
2. Якщо є прогалини - які теми повторити (1-2 речення)
3. На що звернути увагу при поясненні (1-2 речення)
{teacher_recap_note}

Пиши стисло. БЕЗ вкладених списків, БЕЗ детальних покрокових інструкцій.

Відповідай у форматі JSON:
{{
    "title": "Назва теми",
    "contents": "Навчальний матеріал (Markdown), АДАПТОВАНИЙ до рівня {level_info['name']}",
    "teacher_notes": "Рекомендації на основі даних"
}}"""

    return prompt


def build_individual_notes_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    student_info: dict | None = None,
    aggregated_gaps: dict | None = None,
    level: str | None = None,
    missed_prereqs: list[str] | None = None,
) -> str:
    """
    Build prompt for generating notes for specific students (EP3.2).

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context (may include prereq context section)
        student_info: (deprecated) Dict with single student's data - use aggregated_gaps
        aggregated_gaps: Dict from aggregate_student_gaps() with detailed statistics
        level: Target level for the notes (weak/medium/strong)
        missed_prereqs: List of prerequisite topics that students missed/struggled with

    Returns:
        Formatted prompt string
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")

    # Determine level from parameters or student_info
    if level is None and student_info:
        level = student_info.get("level", "medium")
    elif level is None:
        level = "medium"

    level_info = LEVEL_DESCRIPTIONS.get(level, LEVEL_DESCRIPTIONS["medium"])

    # Use new aggregated gaps format if available
    gap_section = ""
    if aggregated_gaps:
        gap_section = format_aggregated_gaps(aggregated_gaps)
    elif student_info:
        # Backwards compatibility with old format (single student)
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
        gap_section = f"{problems_text}{missed_text}"

    # Build structure instructions based on whether there are missed prereqs
    has_recap = missed_prereqs and len(missed_prereqs) > 0
    prereq_list = ", ".join(missed_prereqs) if missed_prereqs else ""

    if has_recap:
        structure_instructions = f"""Структура (ОБОВ'ЯЗКОВО дотримуйся!):
1. **## Повторення** - коротке нагадування пропущених/слабких пререквізитів: {prereq_list}
   - Стисло поясни ключові поняття з цих тем
   - Дай 1-2 приклади для кожного пререквізиту
2. **## Урок** - основний матеріал нової теми
   - Теорія: означення, формули, правила
   - Приклади: задачі з розв'язками
   - Підсумок: ключові формули

ВАЖЛИВО: Секція "## Повторення" ОБОВ'ЯЗКОВА, бо учні мають прогалини у пререквізитах!"""
        teacher_recap_note = f"""
ВАЖЛИВО: Учні мають прогалини у пререквізитах ({prereq_list}).
РЕКОМЕНДАЦІЯ: Почніть урок з повторення цих тем. Переконайтесь, що учні розуміють базові поняття перед переходом до нового матеріалу."""
    else:
        structure_instructions = """Структура:
1. **## Урок** - основний матеріал теми
   - Теорія: означення, формули, правила (складність відповідно до рівня!)
   - Приклади: задачі з розв'язками (складність відповідно до рівня!)
   - Підсумок: ключові формули"""
        teacher_recap_note = ""

    prompt = f"""Створи навчальний матеріал для учнів {grade} класу з предмету "{subject}".

## ТЕМА:
{topic_definition}

## РІВЕНЬ УЧНІВ: {level_info['name'].upper()}
Стиль подачі: {level_info['style']}
Фокус: {level_info['focus']}

{gap_section}
## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

## СТРУКТУРА ВІДПОВІДІ:

### TITLE:
Коротка назва теми (1 рядок)

### CONTENTS (навчальний матеріал ДЛЯ УЧНІВ):
КРИТИЧНО ВАЖЛИВО — АДАПТУЙ ДО РІВНЯ "{level_info['name'].upper()}"!
{level_info['style']}
{level_info['focus']}

Формат:
- НЕ пиши "Привіт!", "Друзі!", "Сьогодні ми вивчимо..."
- Починай одразу з матеріалу

{structure_instructions}

### TEACHER_NOTES (нотатки ДЛЯ ВЧИТЕЛЯ):
Коротка характеристика (МАКСИМУМ 10 рядків) у вигляді списку:
1. Рівень учнів (1-2 речення)
2. Якщо є прогалини - які теми повторити (1-2 речення)
3. На що звернути увагу при поясненні (1-2 речення)
{teacher_recap_note}

Пиши стисло. БЕЗ вкладених списків, БЕЗ детальних покрокових інструкцій.

Відповідай у форматі JSON:
{{
    "title": "Назва теми",
    "contents": "Навчальний матеріал (Markdown), АДАПТОВАНИЙ до рівня {level_info['name']}",
    "teacher_notes": "Рекомендації на основі даних"
}}"""

    return prompt
