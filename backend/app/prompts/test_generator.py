"""
EP4: Test Generator Prompt

Generates test questions based on a topic.
Uses planning + parallel batch generation for speed and coherence.
"""

from typing import Optional
from app.rag.prompts import ALGEBRA_RULES, UKRAINIAN_RULES, HISTORY_RULES


# =============================================================================
# System Prompts
# =============================================================================

TEST_GENERATOR_SYSTEM_PROMPT = """Ти — досвідчений український педагог-методист.
Твоя роль — створювати ОДНЕ якісне тестове завдання для учнів 8-9 класів.

КРИТИЧНО ВАЖЛИВО:
- Створюй ТІЛЬКИ ОДНЕ питання (не масив, не тест, а одне питання)
- Відповідай ТІЛЬКИ JSON об'єктом у вказаному форматі
- Всі питання мають бути СТРОГО по вказаній темі
- НЕ виходь за межі теми
- Пиши українською мовою
- Формулюй чітко та однозначно
- НЕ обгортай відповідь у "questions", "title" чи інші структури"""

TEST_PLANNER_SYSTEM_PROMPT = """Ти — експерт з педагогічного дизайну тестів для української школи.
Твоя роль — планувати структуру тесту, який ефективно перевіряє знання учнів.
Ти аналізуєш тему та створюєш план, що забезпечує рівномірне покриття всіх концепцій."""


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


# =============================================================================
# Test Planner Prompt
# =============================================================================

TEST_PLANNER_PROMPT = """Створи план тесту з предмету "{subject}" для учнів {grade} класу.

## ТЕМА ТЕСТУ:
{topic_definition}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context}

## ВИМОГИ ДО ТЕСТУ:
- Легких питань: {easy_count}
- Середніх питань: {medium_count}
- Складних питань: {hard_count}
- Всього: {total_count} питань

## ПРАВИЛА ПЛАНУВАННЯ:

### 1. Виділи ключові концепції (3-5 концепцій)
Проаналізуй тему та визнач основні концепції/підтеми, які потрібно перевірити.

### 2. Розподіли питання по концепціях
Кожна концепція має бути покрита 2-4 питаннями різної складності.

### 3. Обери типи питань для кожної позиції:
- **single_choice**: для перевірки фактів, визначень, простих правил
- **multiple_choice**: для перевірки розуміння зв'язків, вибору кількох правильних варіантів
- **open**: для перевірки вміння пояснювати, обчислювати, формулювати

### 4. Принципи розподілу типів по складності:
- **Легкі**: 60% single_choice, 40% open (прості визначення, базові факти)
- **Середні**: рівномірно всі типи (застосування знань)
- **Складні**: 50% open, 30% multiple_choice, 20% single_choice (аналіз, синтез)

### 5. Уникай:
- Однотипних питань підряд на ту саму концепцію
- Питань, що перевіряють абсолютно те саме
- Занадто схожих формулювань

## ФОРМАТ ВІДПОВІДІ (JSON):
```json
{{
    "concepts": ["концепція1", "концепція2", "концепція3"],
    "question_specs": [
        {{
            "spec_id": 1,
            "difficulty": "easy",
            "question_type": "single_choice",
            "concept": "концепція1",
            "focus": "конкретний аспект для перевірки цим питанням"
        }},
        {{
            "spec_id": 2,
            "difficulty": "medium",
            "question_type": "open",
            "concept": "концепція2",
            "focus": "інший аспект"
        }}
    ],
    "rationale": "Коротке пояснення логіки розподілу (1-2 речення)"
}}
```

ВАЖЛИВО:
- Створи рівно {total_count} специфікацій питань
- Дотримуйся вказаного розподілу: {easy_count} легких, {medium_count} середніх, {hard_count} складних
- Кожна специфікація має унікальний spec_id (від 1 до {total_count})
- Надай ТІЛЬКИ JSON, без додаткового тексту."""


def build_planner_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    easy_count: int,
    medium_count: int,
    hard_count: int,
) -> str:
    """
    Build the test planning prompt.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context
        easy_count: Number of easy questions
        medium_count: Number of medium questions
        hard_count: Number of hard questions

    Returns:
        Formatted prompt string for test planning
    """
    total_count = easy_count + medium_count + hard_count

    return TEST_PLANNER_PROMPT.format(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context if context else "Контекст не знайдено. Використовуй власні знання про тему.",
        easy_count=easy_count,
        medium_count=medium_count,
        hard_count=hard_count,
        total_count=total_count,
    )


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


def build_single_question_prompt(
    subject: str,
    grade: int,
    topic: str,
    context: str,
    difficulty: str,
    question_type: str,
    concept: Optional[str] = None,
    focus: Optional[str] = None,
) -> str:
    """
    Build prompt for generating exactly ONE question.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic: Topic description
        context: Retrieved textbook context
        difficulty: "easy", "medium", or "hard"
        question_type: "multiple_choice" or "open"
        concept: Specific concept to assess (from planner)
        focus: Specific aspect to test (from planner)

    Returns:
        Formatted prompt string for single question generation
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")
    diff_info = DIFFICULTY_DESCRIPTIONS.get(difficulty, DIFFICULTY_DESCRIPTIONS["medium"])

    # Build concept-focused instruction if provided
    concept_instruction = ""
    if concept and focus:
        concept_instruction = f"""
## ФОКУС ПИТАННЯ:
- Концепція: {concept}
- Аспект для перевірки: {focus}
- Питання ПОВИННО перевіряти саме цей аспект концепції!
"""
    elif concept:
        concept_instruction = f"""
## ФОКУС ПИТАННЯ:
- Концепція: {concept}
- Питання має перевіряти розуміння цієї концепції.
"""

    if question_type in {"multiple_choice", "single_choice"}:
        format_instructions = """## ПРОЦЕС СТВОРЕННЯ ПИТАННЯ:

КРОК 1: Спочатку продумай питання та ПРАВИЛЬНУ ВІДПОВІДЬ
- Яке конкретне знання перевіряємо?
- Яка правильна відповідь і ЧОМУ?

КРОК 2: Створи 3 НЕПРАВИЛЬНІ але правдоподібні варіанти
- Типові помилки учнів
- Схожі але неправильні відповіді

КРОК 3: Визнач позицію правильної відповіді (0-3)

## ОБОВ'ЯЗКОВИЙ JSON ФОРМАТ:
```json
{
    "reasoning": "Коротко: правильна відповідь X тому що Y",
    "question": "Текст питання?",
    "options": [
        "Варіант 0",
        "Варіант 1",
        "Варіант 2",
        "Варіант 3"
    ],
    "correct_answer_index": 0,
    "explanation": "Пояснення для учня",
    "topic": "Підтема"
}
```

⚠️ КРИТИЧНІ ВИМОГИ:
1. "reasoning" — ОБОВ'ЯЗКОВО спочатку напиши яка відповідь правильна і чому!
2. "options" ОБОВ'ЯЗКОВО містить РІВНО 4 елементи
3. "correct_answer_index" — ЧИСЛО 0-3, має відповідати reasoning!
4. Всі 4 варіанти різні та правдоподібні
5. Тільки ОДИН варіант правильний

ПРИКЛАД:
```json
{
    "reasoning": "При D > 0 квадратне рівняння має 2 корені. Правильна відповідь - індекс 2.",
    "question": "Скільки коренів має квадратне рівняння з додатним дискримінантом?",
    "options": [
        "Жодного кореня",
        "Один корінь",
        "Два корені",
        "Три корені"
    ],
    "correct_answer_index": 2,
    "explanation": "При D > 0 квадратне рівняння має два різні дійсні корені",
    "topic": "Квадратні рівняння"
}
```"""
    else:
        format_instructions = """## ПРОЦЕС СТВОРЕННЯ ПИТАННЯ:

КРОК 1: Продумай питання та його ПРАВИЛЬНУ ВІДПОВІДЬ
- Яке знання/вміння перевіряємо?
- Яка очікувана відповідь?

КРОК 2: Сформулюй питання чітко

## ОБОВ'ЯЗКОВИЙ JSON ФОРМАТ:
```json
{
    "reasoning": "Спочатку розв'яжу задачу: ... Відповідь: ...",
    "question": "Текст відкритого питання?",
    "explanation": "Коротка очікувана відповідь",
    "topic": "Підтема"
}
```

⚠️ КРИТИЧНІ ВИМОГИ:
1. "reasoning" — ОБОВ'ЯЗКОВО спочатку розв'яжи задачу сам!
2. "question" — чітке питання з конкретною відповіддю
3. "explanation" — КОРОТКА відповідь (макс 100 слів), лише результат + 1-2 кроки
4. Питання НЕ має бути занадто загальним

ПРИКЛАД:
```json
{
    "reasoning": "Розв'язую: y = 5 - x, підставляю: x - (5-x) = 1, 2x = 6, x = 3, y = 2",
    "question": "Розв'яжіть систему рівнянь методом підстановки: x + y = 5, x - y = 1",
    "explanation": "Відповідь: x = 3, y = 2. З першого рівняння y = 5 - x, підставляємо в друге.",
    "topic": "Системи рівнянь"
}
```"""

    type_name = "з вибором відповіді" if question_type in {"multiple_choice", "single_choice"} else "відкритого типу"

    prompt = f"""Створи ОДНЕ тестове питання {type_name} рівня "{diff_info['name'].upper()}" для учнів {grade} класу з предмету "{subject}".

## ТЕМА (питання ТІЛЬКИ по цій темі!):
{topic}
{concept_instruction}
## РІВЕНЬ СКЛАДНОСТІ: {diff_info['name'].upper()}
- {diff_info['description']}
- Приклади: {diff_info['examples']}

## ПРАВИЛА ТА ФОРМУЛИ:
{subject_rules if subject_rules else "Використовуй стандартні правила для цього предмету."}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context if context else "Контекст не знайдено. Використовуй власні знання."}

{format_instructions}

⚠️ УВАГА: Надай ТІЛЬКИ валідний JSON об'єкт БЕЗ будь-якого тексту до чи після нього!
Відповідь має починатися з {{ і закінчуватися на }}"""

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
    DEPRECATED: Use build_single_question_prompt instead.
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
