"""
EP4: Test Generator Prompt

Generates test questions based on a topic.
Uses planning + parallel batch generation for speed and coherence.
"""

from typing import Optional, Dict, Any
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
- НЕ обгортай відповідь у "questions", "title" чи інші структури

МАТЕМАТИЧНІ ФОРМУЛИ (для Алгебри та математичних предметів):
- ЗАВЖДИ використовуй LaTeX для формул, виразів, рівнянь
- ОБОВ'ЯЗКОВО обгортай формули в \\(...\\) — інакше вони НЕ відобразяться!
- КРИТИЧНО: НЕ змішуй делімітери! \\( закривається ТІЛЬКИ \\), НЕ $$, НЕ \\]
- Дроби: \\(\\frac{чисельник}{знаменник}\\)
- Степені: \\(x^2\\), \\(a^{n+1}\\)
- Корені: \\(\\sqrt{x}\\), \\(\\sqrt[3]{x}\\)
- Грецькі літери: \\(\\alpha\\), \\(\\beta\\), \\(\\Delta\\)
- Індекси: \\(a_n\\), \\(x_{i+1}\\)
- НЕ пиши формули звичайним текстом — ТІЛЬКИ LaTeX!
- НЕ використовуй \\\\ для переносу рядків
- ВАРІАНТИ ВІДПОВІДЕЙ: обгортай формули в \\(...\\)"""

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
# Level Guidance for Test Generation
# =============================================================================

LEVEL_GUIDANCE = {
    "weak": "Створюй питання з простішими формулюваннями. Уникай багатокрокових задач. Фокусуйся на базових поняттях.",
    "medium": "Збалансуй прості та складніші питання. Включай типові задачі на застосування знань.",
    "strong": "Включай питання, що вимагають глибшого розуміння та аналізу. Додавай нестандартні формулювання.",
}


# =============================================================================
# Test Planner Prompt (Level-Aware, No Difficulty Counts)
# =============================================================================

TEST_PLANNER_PROMPT = """Створи план тесту з предмету "{subject}" для учнів {grade} класу.

## ТЕМА ТЕСТУ:
{topic_definition}

## МАТЕРІАЛ З ПІДРУЧНИКА:
{context}

## РІВЕНЬ УЧНІВ: {level}
{level_guidance}

## ВИМОГИ ДО ТЕСТУ:
- Створи рівно 12 специфікацій питань
- Кожне питання має УНІКАЛЬНИЙ фокус — різні аспекти теми
- ~50% single_choice, ~20% multiple_choice, ~30% open

## ПРАВИЛА ПЛАНУВАННЯ:

### 1. Обери типи питань для кожної позиції:
- **single_choice**: для перевірки фактів, визначень, простих правил
- **multiple_choice**: для перевірки розуміння зв'язків, вибору кількох правильних варіантів
- **open**: для перевірки вміння пояснювати, обчислювати, формулювати

### 2. КРИТИЧНО — Визнач УНІКАЛЬНИЙ фокус для кожного питання:
- Фокус — це КОНКРЕТНИЙ аспект теми: формула, властивість, метод, застосування
- ⚠️ ЗАБОРОНЕНО повторювати однаковий фокус у різних питаннях!
- ⚠️ Якщо фокус "формула дискримінанта" вже є — НЕ МОЖНА створювати інше питання про формулу дискримінанта
- Приклади РІЗНИХ фокусів для однієї теми:
  - "формула дискримінанта" (1 питання)
  - "знак дискримінанта та кількість коренів" (інше питання)
  - "обчислення дискримінанта для конкретного рівняння" (ще інше)
  - "формула коренів через дискримінант" (ще інше)

### 3. Перевір перед завершенням:
- Переглянь всі 12 фокусів — вони мають бути РІЗНИМИ
- Жодні два питання не повинні перевіряти те саме знання

## ФОРМАТ ВІДПОВІДІ (JSON):
```json
{{
    "question_specs": [
        {{
            "spec_id": 1,
            "question_type": "single_choice",
            "focus": "конкретний аспект: формула/властивість/метод"
        }},
        {{
            "spec_id": 2,
            "question_type": "open",
            "focus": "ІНШИЙ конкретний аспект"
        }}
    ],
    "rationale": "Коротке пояснення логіки розподілу (1-2 речення)"
}}
```

ВАЖЛИВО:
- Створи рівно 12 специфікацій питань
- Кожна специфікація має унікальний spec_id (від 1 до 12)
- ⚠️ Кожен focus має бути УНІКАЛЬНИМ — не повторюй однакові аспекти!
- НЕ вказуй difficulty — складність визначається автоматично
- Надай ТІЛЬКИ JSON, без додаткового тексту."""


def build_planner_prompt(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    level: str = "medium",
) -> str:
    """
    Build the test planning prompt.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        context: Retrieved textbook context
        level: Student level for guidance ("weak", "medium", "strong")

    Returns:
        Formatted prompt string for test planning
    """
    level_guidance = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["medium"])

    return TEST_PLANNER_PROMPT.format(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context if context else "Контекст не знайдено. Використовуй власні знання про тему.",
        level=level,
        level_guidance=level_guidance,
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
    question_type: str,
    focus: Optional[str] = None,
    level: str = "medium",
    difficulty: str = "medium",
) -> str:
    """
    Build prompt for generating exactly ONE question.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        topic: Topic description
        context: Retrieved textbook context
        question_type: "multiple_choice", "single_choice", or "open"
        focus: Specific aspect to test (from planner)
        level: Student level for subtle guidance ("weak", "medium", "strong")
        difficulty: Target difficulty level ("easy", "medium", "hard")

    Returns:
        Formatted prompt string for single question generation
    """
    subject_rules = SUBJECT_RULES_MAP.get(subject, "")
    level_guidance = LEVEL_GUIDANCE.get(level, LEVEL_GUIDANCE["medium"])

    # Build difficulty instruction
    difficulty_labels = {
        "easy": "ЛЕГКЕ (базовий рівень)",
        "medium": "СЕРЕДНЄ (достатній рівень)",
        "hard": "СКЛАДНЕ (високий рівень)",
    }
    difficulty_label = difficulty_labels.get(difficulty, difficulty_labels["medium"])

    # Get subject-specific difficulty criteria
    subject_criteria = get_subject_difficulty_criteria(subject, grade)

    # Build focus instruction if provided
    focus_instruction = ""
    if focus:
        focus_instruction = f"""
## ФОКУС ПИТАННЯ:
- Аспект для перевірки: {focus}
- Питання ПОВИННО перевіряти саме цей аспект теми!
"""

    # Build difficulty instruction
    difficulty_instruction = f"""
## РІВЕНЬ СКЛАДНОСТІ: {difficulty_label}
Питання ОБОВ'ЯЗКОВО має відповідати цьому рівню складності!

{subject_criteria}
"""

    if question_type == "single_choice":
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
    elif question_type == "multiple_choice":
        format_instructions = """## ПРОЦЕС СТВОРЕННЯ ПИТАННЯ:

КРОК 1: Спочатку продумай питання з КІЛЬКОМА ПРАВИЛЬНИМИ ВІДПОВІДЯМИ
- Яке конкретне знання перевіряємо?
- Які відповіді правильні і ЧОМУ? (мінімум 2, максимум 3)

КРОК 2: Створи неправильні варіанти (щоб було рівно 4)
- Типові помилки учнів
- Схожі але неправильні відповіді

КРОК 3: Визнач позиції ВСІХ правильних відповідей (масив чисел 0-3)

## ОБОВ'ЯЗКОВИЙ JSON ФОРМАТ:
```json
{
    "reasoning": "Коротко: правильні відповіді X і Y тому що Z",
    "question": "Текст питання? (Оберіть кілька правильних відповідей)",
    "options": [
        "Варіант 0",
        "Варіант 1",
        "Варіант 2",
        "Варіант 3"
    ],
    "correct_answer_indices": [0, 2],
    "explanation": "Пояснення для учня",
    "topic": "Підтема"
}
```

⚠️ КРИТИЧНІ ВИМОГИ:
1. "reasoning" — ОБОВ'ЯЗКОВО спочатку напиши які відповіді правильні і чому!
2. "options" ОБОВ'ЯЗКОВО містить РІВНО 4 елементи
3. "correct_answer_indices" — МАСИВ з 2-3 числами 0-3 (кілька правильних!)
4. Всі 4 варіанти різні та правдоподібні
5. МІНІМУМ 2 правильні відповіді, МАКСИМУМ 3

ПРИКЛАД:
```json
{
    "reasoning": "Властивості квадратного кореня: √(ab) = √a·√b, √(a/b) = √a/√b. Правильні індекси 0 і 2.",
    "question": "Які з наступних тверджень про квадратні корені є правильними? (Оберіть кілька)",
    "options": [
        "√(ab) = √a · √b для a,b ≥ 0",
        "√(a+b) = √a + √b для a,b ≥ 0",
        "√(a/b) = √a / √b для a ≥ 0, b > 0",
        "√(a-b) = √a - √b для a ≥ b ≥ 0"
    ],
    "correct_answer_indices": [0, 2],
    "explanation": "Корінь добутку/частки дорівнює добутку/частці коренів, але корінь суми/різниці НЕ дорівнює сумі/різниці коренів",
    "topic": "Властивості квадратних коренів"
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

    if question_type == "single_choice":
        type_name = "з однією правильною відповіддю"
    elif question_type == "multiple_choice":
        type_name = "з КІЛЬКОМА правильними відповідями"
    else:
        type_name = "відкритого типу"

    prompt = f"""Створи ОДНЕ тестове питання {type_name} для учнів {grade} класу з предмету "{subject}".

## ТЕМА (питання ТІЛЬКИ по цій темі!):
{topic}
{focus_instruction}{difficulty_instruction}
## РЕКОМЕНДАЦІЇ ДО СТИЛЮ:
{level_guidance}

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


# =============================================================================
# Difficulty Classifier Prompt (Batch Classification)
# =============================================================================

DIFFICULTY_CLASSIFIER_BATCH_PROMPT = """Ти — експерт з оцінювання складності тестових завдань для {grade} класу з предмету "{subject}".

## ЗАВДАННЯ:
Класифікуй складність КОЖНОГО з {num_questions} питань нижче.

ВАЖЛИВО: Використовуй ВСІ три рівні! Розподіл має бути приблизно:
- ~25-35% питань = EASY
- ~35-45% питань = MEDIUM
- ~25-35% питань = HARD

НЕ бійся ставити "hard" — якщо питання вимагає кількох кроків або глибокого аналізу, це HARD!

## КРИТЕРІЇ КЛАСИФІКАЦІЇ ДЛЯ {subject}:

{subject_criteria}

## ПИТАННЯ ДЛЯ КЛАСИФІКАЦІЇ:

{questions_text}

## ФОРМАТ ВІДПОВІДІ (JSON):
```json
{{
    "classifications": [
        {{"spec_id": 1, "difficulty": "easy|medium|hard", "reasoning": "1 речення"}},
        {{"spec_id": 2, "difficulty": "easy|medium|hard", "reasoning": "1 речення"}},
        ...
    ]
}}
```

ВАЖЛИВО:
1. Класифікуй ВСІ {num_questions} питань
2. Використай ВСІ три рівні складності (easy, medium, hard)
3. Якщо сумніваєшся між medium і hard — обери HARD
4. Надай ТІЛЬКИ JSON, без додаткового тексту"""


ALGEBRA_DIFFICULTY_CRITERIA = """### Алгебра {grade} клас:

**EASY** (базовий рівень):
- Пряма підстановка у формулу (наприклад, знайти значення виразу при x=2)
- Визначення терміну (що таке дискримінант?)
- Одна проста операція (спростити 2x + 3x)
- Впізнавання формули чи графіка

**MEDIUM** (достатній рівень):
- Розв'язування типового рівняння за алгоритмом
- Застосування 2-3 формул послідовно
- Побудова графіка за формулою
- Стандартні текстові задачі

**HARD** (високий рівень):
- Рівняння/нерівності з параметром
- Нестандартні формулювання (задачі "навпаки")
- Доведення властивостей чи тверджень
- Комбінування тем (наприклад, системи + квадратні рівняння)
- Дослідження функцій (область визначення + множина значень + монотонність)
- Текстові задачі з кількома невідомими"""


UKRAINIAN_DIFFICULTY_CRITERIA = """### Українська мова {grade} клас:

**EASY** (базовий рівень):
- Визначення частини мови, члена речення
- Базове правило (ненаголошене е/и)
- Впізнавання мовного явища
- Просте визначення терміну

**MEDIUM** (достатній рівень):
- Застосування правила до конкретного випадку
- Виправлення помилки з поясненням
- Визначення синтаксичної ролі слова в контексті
- Трансформація речення (активне ↔ пасивне)

**HARD** (високий рівень):
- Правопис складних випадків (апостроф + м'який знак)
- Пунктуація у складних реченнях з різними видами зв'язку
- Стилістичний аналіз тексту
- Винятки з правил та їх застосування
- Розрізнення омонімічних форм (однакові слова — різні частини мови)
- Комплексний аналіз речення"""


HISTORY_DIFFICULTY_CRITERIA = """### Історія України {grade} клас:

**EASY** (базовий рівень):
- Відома дата або подія (коли була Переяславська рада?)
- Впізнавання історичної постаті за описом
- Прості факти з підручника
- Хронологічне впорядкування 2-3 подій

**MEDIUM** (достатній рівень):
- Причинно-наслідкові зв'язки (чому сталося X?)
- Порівняння двох подій/періодів
- Наслідки події для України
- Роль особи в історичному процесі

**HARD** (високий рівень):
- Аналіз історичного джерела (документу, карти)
- Оцінка значення події для подальшої історії
- Альтернативні точки зору на подію
- Маловідомі факти та деталі
- Зв'язок подій з ширшим європейським контекстом
- Порівняння оцінок істориків"""


def get_subject_difficulty_criteria(subject: str, grade: int) -> str:
    """Get subject-specific difficulty criteria."""
    if "Алгебра" in subject or "алгебра" in subject:
        return ALGEBRA_DIFFICULTY_CRITERIA.format(grade=grade)
    elif "Українська" in subject or "українська" in subject:
        return UKRAINIAN_DIFFICULTY_CRITERIA.format(grade=grade)
    elif "Історія" in subject or "історія" in subject:
        return HISTORY_DIFFICULTY_CRITERIA.format(grade=grade)
    else:
        # Generic criteria
        return f"""### {subject} {grade} клас:

**EASY**: Базові визначення, прості факти, пряме застосування правил
**MEDIUM**: Типові задачі, застосування знань, порівняння
**HARD**: Аналіз, синтез, нестандартні формулювання, комбінування тем"""


def build_difficulty_classifier_prompt(
    subject: str,
    grade: int,
    question: Dict[str, Any],
) -> str:
    """
    Build prompt for classifying a single question's difficulty.

    DEPRECATED: Use build_batch_difficulty_classifier_prompt for better results.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        question: Question dict with at least "question" field

    Returns:
        Formatted prompt string for difficulty classification
    """
    question_text = question.get("question", "")

    # Include options if it's a multiple choice question
    if question.get("options"):
        options_text = "\n".join(f"  {i}) {opt}" for i, opt in enumerate(question["options"]))
        question_text = f"{question_text}\n\nВаріанти відповідей:\n{options_text}"

    subject_criteria = get_subject_difficulty_criteria(subject, grade)

    # Single question version of the prompt
    single_prompt = f"""Визнач рівень складності цього питання для учня {grade} класу з предмету "{subject}".

## ПИТАННЯ:
{question_text}

## КРИТЕРІЇ КЛАСИФІКАЦІЇ:

{subject_criteria}

## ВАЖЛИВО:
- Якщо питання вимагає кількох кроків або глибокого розуміння — це HARD
- Не бійся ставити "hard" для справді складних питань!
- "medium" — тільки для типових задач на застосування

## ФОРМАТ ВІДПОВІДІ (JSON):
{{"difficulty": "easy|medium|hard", "reasoning": "коротке пояснення (1 речення)"}}

Надай ТІЛЬКИ JSON, без додаткового тексту."""

    return single_prompt


def build_batch_difficulty_classifier_prompt(
    subject: str,
    grade: int,
    questions: list[Dict[str, Any]],
) -> str:
    """
    Build prompt for batch classification of multiple questions.

    This produces better difficulty distribution than single-question classification.

    Args:
        subject: Subject name in Ukrainian
        grade: Grade level (8 or 9)
        questions: List of question dicts with "question" and "spec_id" fields

    Returns:
        Formatted prompt string for batch difficulty classification
    """
    # Format questions for the prompt
    questions_parts = []
    for q in questions:
        spec_id = q.get("spec_id", 0)
        q_text = q.get("question", "")
        q_type = q.get("type", "open")

        part = f"### Питання {spec_id} ({q_type}):\n{q_text}"

        # Include options for choice questions
        if q.get("options"):
            options_text = "\n".join(f"   {chr(65+i)}) {opt}" for i, opt in enumerate(q["options"]))
            part += f"\nВаріанти:\n{options_text}"

        questions_parts.append(part)

    questions_text = "\n\n".join(questions_parts)
    subject_criteria = get_subject_difficulty_criteria(subject, grade)

    return DIFFICULTY_CLASSIFIER_BATCH_PROMPT.format(
        subject=subject,
        grade=grade,
        num_questions=len(questions),
        subject_criteria=subject_criteria,
        questions_text=questions_text,
    )
