"""
Solver Service - Unified Solver-Based Validation.

Self-contained validation module based on agent.py V7:
- Own RAG retrieval (BM25 + Vector hybrid)
- Subject-specific expert prompts
- Answer extraction and comparison

Same flow for MC and Open questions:
1. Retrieve context using hybrid RAG
2. Solver solves the question WITHOUT seeing the expected answer
3. Compare solver's answer to expected answer
4. Match = Valid, Mismatch = Invalid
"""

import logging
import re
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from app.rag.utils.llm_client import get_llm_client, generate_json_safe
from app.rag.utils.hybrid_retriever import get_retriever, format_context

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration (from agent.py)
# =============================================================================

RETRIEVAL_TOP_K = 4
CONTEXT_MAX_CHARS = {
    "Алгебра": 4500,
    "Українська мова": 5000,
    "Історія України": 3500,
}
DEFAULT_CONTEXT_MAX_CHARS = 4500


def _get_context_limit(subject: str) -> int:
    return CONTEXT_MAX_CHARS.get(subject, DEFAULT_CONTEXT_MAX_CHARS)


@dataclass
class CheckResult:
    """Result of question validation."""
    is_valid: bool
    reason: str
    confidence: float = 0.0
    solver_answer: Optional[str] = None      # "A" or "A,C" or text
    expected_answer: Optional[str] = None    # "A" or "A,C" or text
    is_rejected: bool = False                # True if solver said INVALID
    rejection_reason: Optional[str] = None   # Why solver rejected


# =============================================================================
# Subject-Specific Solver Prompts (copied from agent.py)
# =============================================================================

SOLVER_PROMPT_MATH = """Ти — досвідчений репетитор з математики для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

ІНСТРУКЦІЇ:
1. Уважно прочитай математичне питання і всі формули
2. Зверни увагу на LaTeX-нотацію: \\(x\\) — це змінна x, \\(\\frac{{a}}{{b}}\\) — це дріб a/b
3. Використай довідковий матеріал для перевірки формул та визначень
4. Покроково обмірковуй розв'язок і вибери правильну відповідь: A, B, C або D

ПРИКЛАДИ:

Питання: Чому дорівнює знаменник геометричної прогресії \\((b_n)\\), якщо \\(b_1=56, b_2=7\\)?
Варіанти: A) 8  B) 49  C) –8  D) \\(\\frac{{1}}{{8}}\\)

Міркування: Знаменник q = b₂/b₁ = 7/56 = 1/8
Відповідь: D

---

Питання: Знайдіть множину розв'язків нерівності (x+6)²<0
Варіанти: A) R  B) −6  C) 6  D) ∅

Міркування: Квадрат завжди ≥ 0, тому (x+6)² < 0 неможливо. Розв'язків немає (∅).
Відповідь: D

---

Питання: Розв'яжіть рівняння 3x - 7 = 5
Варіанти: A) 2  B) 4  C) -2/3  D) 12/3

Міркування: 3x - 7 = 5 → 3x = 12 → x = 4
Відповідь: B

---

Питання: Область визначення функції f(x) = 1/(x-3)?
Варіанти: A) x ≠ 3  B) x ≥ 3  C) x > 0  D) x ∈ R

Міркування: Знаменник не може дорівнювати нулю, тому x - 3 ≠ 0 → x ≠ 3
Відповідь: A

---

## ЗАДАЧА ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Розв'яжи покроково і дай відповідь у форматі:
Міркування: ...
Відповідь: A/B/C/D або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Жоден варіант не є правильним
- Кілька варіантів правильні одночасно
- Питання містить фактичні помилки"""


SOLVER_PROMPT_UKRAINIAN = """Ти — досвідчений репетитор української мови для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

ІНСТРУКЦІЇ:
1. Уважно прочитай питання про граматику, синтаксис чи пунктуацію
2. Використай довідковий матеріал для перевірки термінів та правил
3. Звернися до ТОЧНИХ визначень термінів
4. Вибери правильну відповідь: A, B, C або D

ПРИКЛАДИ:

Питання: Односкладним називним є речення
Варіанти: A) Теплий вітерець повіяв.  B) Холодний день.  C) Камінь холодний  D) Сьогодні холодний день.

Міркування: Односкладне називне має тільки підмет (іменник у називному). "Холодний день" — це воно.
Відповідь: B

---

Питання: Тире, тому що речення неповне, вжито в реченні:
Варіанти: A) Життя – це боротьба.  B) Боротись – значить жить.  C) Життя триває довго, щастя – мить.  D) І чебрець, і м'яту... – усе вирощувала мати.

Міркування: "щастя [триває] мить" — пропущене дієслово, тому тире.
Відповідь: C

---

Питання: Безсполучниковим складним є речення:
Варіанти: A) Я думаю, що він прав.  B) Сніг падав, вітер свистів.  C) Дощ йшов, але швидко припинився.  D) Той, хто прийшов першим, виграв.

Міркування: Безсполучникові - це складні речення без сполучників (і, та, але, що).
B) 'Сніг падав, вітер свистів' - дві частини з'єднані тільки комою, без сполучників.
Відповідь: B

---

Питання: Немає додатка в такому реченні:
Варіанти: A) Посадила мати три ясени в полі.  B) Читати я навчився в п'ять років.  C) Мені годі думати про порятунок.  D) Довженко став відомим режисером.

Міркування: Додаток - другорядний член, що відповідає на питання непрямих відмінків (кого? чого? кому? чому? ким? чим?).
D) 'режисером' - це іменна частина складеного присудка, а не додаток.
Відповідь: D

---

## ПИТАННЯ ({grade} клас):
{question}

## ВАРІАНТИ:
{options}

Проаналізуй кожен варіант і дай відповідь у форматі:
Міркування: ...
Відповідь: A/B/C/D або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Жоден варіант не є правильним
- Кілька варіантів правильні одночасно
- Питання містить фактичні помилки"""


SOLVER_PROMPT_HISTORY = """Ти — досвідчений репетитор історії України для учнів 8-9 класів.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

ІНСТРУКЦІЇ:
1. Уважно прочитай питання про історичні події, дати, постаті
2. Звернися до довідкового матеріалу для перевірки дат, імен, подій
3. При порівнянні дат — шукай хронологічну послідовність
4. Вибери правильну відповідь: A, B, C або D

ПРИКЛАДИ:

Питання: Яка подія відбулася найраніше?
Варіанти: A) Корсунська битва  B) Пилявецька битва  C) Жовтоводська битва  D) Зборівська битва

Міркування: Хронологія: Жовтоводська (1648, квітень) → Корсунська (1648, травень) → Зборівська (1649).
Відповідь: C

---

Питання: У якому році відбувся перший поділ Речі Посполитої?
Варіанти: A) 1772 р.  B) 1775 р.  C) 1793 р.  D) 1795 р.

Міркування: Три поділи: 1772 (перший), 1793 (другий), 1795 (третій).
Відповідь: A

---

## ПИТАННЯ (Історія України, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

Знайди в контексті факти і дай відповідь у форматі:
Міркування: ...
Відповідь: A/B/C/D або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Жоден варіант не є правильним
- Кілька варіантів правильні одночасно
- Питання містить фактичні помилки"""


SOLVER_PROMPT_DEFAULT = """## КОНТЕКСТ З ПІДРУЧНИКА:
{context}

---

## ПИТАННЯ ({subject}, {grade} клас):
{question}

## ВАРІАНТИ:
{options}

---

Знайди в контексті правило або факт для відповіді.
Проаналізуй кожен варіант.

Дай відповідь у форматі:
Міркування: ...
Відповідь: A/B/C/D або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Жоден варіант не є правильним
- Кілька варіантів правильні одночасно
- Питання містить фактичні помилки"""


# Subject to prompt mapping
SOLVER_PROMPTS = {
    "Українська мова": SOLVER_PROMPT_UKRAINIAN,
    "Алгебра": SOLVER_PROMPT_MATH,
    "Геометрія": SOLVER_PROMPT_MATH,
    "Історія України": SOLVER_PROMPT_HISTORY,
    "Всесвітня історія": SOLVER_PROMPT_HISTORY,
}


# =============================================================================
# Multiple Choice Prompt (2-3 correct answers)
# =============================================================================

SOLVER_PROMPT_MULTIPLE = """Ти — експерт з предмету {subject} для {grade} класу.

ДОВІДКОВИЙ МАТЕРІАЛ:
{context}
---

## ПИТАННЯ (вибери 2-3 правильні відповіді):
{question}

## ВАРІАНТИ:
{options}

ІНСТРУКЦІЇ:
1. Проаналізуй кожен варіант окремо
2. Вибери ВСІ правильні відповіді (зазвичай 2-3)
3. Якщо питання некоректне — відповідай INVALID

Міркування: ...
Відповідь: A,C (перелічи всі правильні через кому) або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Менше 2 варіантів правильні
- Всі 4 варіанти правильні
- Питання містить фактичні помилки"""


# =============================================================================
# Open Question Solver Prompt
# =============================================================================

OPEN_SOLVER_PROMPT = """Ти — експерт з предмету {subject} для {grade} класу.

## Контекст з підручника
{context}

---

## Питання
{question}

---

ІНСТРУКЦІЇ:
1. Уважно прочитай питання
2. Використай контекст для формування відповіді
3. Дай коротку, конкретну відповідь
4. Якщо питання некоректне — відповідай INVALID

Міркування: ...
Відповідь: ... або INVALID

Відповідай INVALID якщо:
- Питання неоднозначне або незрозуміле
- Неможливо дати однозначну відповідь
- Питання містить фактичні помилки"""


# =============================================================================
# Answer Comparison Prompt (for Open questions)
# =============================================================================

ANSWER_COMPARISON_PROMPT = """Порівняй дві відповіді на питання.

## Питання
{question}

## Очікувана відповідь
{expected}

## Відповідь для перевірки
{solver_answer}

## Завдання
Визнач, чи відповіді ЕКВІВАЛЕНТНІ за змістом.

Відповіді ЕКВІВАЛЕНТНІ, якщо:
- Передають ТУ САМУ ключову інформацію/результат
- Відрізняються лише формою запису (0.5 = 1/2, "у 1918 році" = "1918 р.")
- Одна коротша, інша детальніша, але СУТЬ однакова
- Використовують синоніми чи перефразування

НЕ вважай різними:
- Різні формати чисел: -0.5 і -1/2, 25% і 0.25
- Короткі vs повні відповіді з тим самим результатом
- Різний порядок перелічення (якщо питання не вимагає порядку)

JSON: {{"match": true/false, "reason": "коротке пояснення"}}"""


# =============================================================================
# Helper Functions
# =============================================================================

def _format_options(options: List[str]) -> str:
    """Format options for solver prompt (A/B/C/D format like agent.py)."""
    letters = ["A", "B", "C", "D"]
    return "\n".join([f"{letters[i]}) {opt}" for i, opt in enumerate(options[:4])])


def _get_solver_prompt(subject: str) -> str:
    """Get subject-specific solver prompt."""
    return SOLVER_PROMPTS.get(subject, SOLVER_PROMPT_DEFAULT)


def _extract_answer(response: str, allow_multiple: bool = False) -> str:
    """Extract answer letter(s) from solver response.

    Args:
        response: LLM response text
        allow_multiple: If True, extract multiple letters (for multiple_choice)

    Returns:
        - "INVALID" if solver rejected the question
        - Single letter "A" for single_choice
        - Comma-separated "A,C" for multiple_choice
        - Empty string if no answer found
    """
    if not response:
        return ""

    # Check for INVALID first
    if re.search(r'\bINVALID\b', response, re.IGNORECASE):
        return "INVALID"

    # Multiple patterns in priority order
    patterns = [
        # "Відповідь: A" or "Відповідь - A" or "Відповідь: A, C"
        r'Відповідь[:\s\-–—]+([ABCD][,\s]*(?:[ABCD][,\s]*)*)',
        # "Правильна відповідь: A"
        r'[Пп]равильна\s+відповідь[:\s\-–—]+([ABCD][,\s]*(?:[ABCD][,\s]*)*)',
        # "Отже, A" / "Тому A"
        r'(?:Отже|Тому)[,:\s]+([ABCD])\b',
        # **A** markdown bold
        r'\*\*([ABCD])\*\*',
        # "варіант A" or "варіант: A"
        r'варіант[:\s]+([ABCD])\b',
        # "відповідь A" (without colon)
        r'відповідь\s+([ABCD])\b',
        # Letter at end of response with optional punctuation
        r'\b([ABCD])\s*[.!]?\s*$',
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE | re.MULTILINE)
        if match:
            letters = re.findall(r'[ABCD]', match.group(1).upper())
            if letters:
                if allow_multiple:
                    return ",".join(sorted(set(letters)))
                return letters[0]

    # Fallback: find standalone letters, take the last one
    letters = re.findall(r'\b([ABCD])\b', response)
    if letters:
        if allow_multiple:
            return ",".join(sorted(set(letters)))
        return letters[-1].upper()

    return ""


def _letter_to_index(letter: str) -> int:
    """Convert letter (A/B/C/D) to index (0/1/2/3)."""
    mapping = {"A": 0, "B": 1, "C": 2, "D": 3}
    return mapping.get(letter.upper(), 0)


def _index_to_letter(index: int) -> str:
    """Convert index (0/1/2/3) to letter (A/B/C/D)."""
    letters = ["A", "B", "C", "D"]
    return letters[index] if 0 <= index < 4 else "A"


def _indices_to_letters(indices: List[int]) -> str:
    """Convert list of indices to comma-separated letters."""
    letters = [_index_to_letter(i) for i in sorted(indices)]
    return ",".join(letters)


def _letters_to_indices(letters_str: str) -> List[int]:
    """Convert comma-separated letters to list of indices."""
    letters = letters_str.split(",")
    return sorted([_letter_to_index(l.strip()) for l in letters if l.strip()])


def _extract_rejection_reason(response: str) -> Optional[str]:
    """Extract rejection reason from solver response."""
    # Try to find reason after INVALID
    patterns = [
        r'INVALID[:\s]+(.+?)(?:\n|$)',
        r'Причина:\s*(.+?)(?:\n|$)',
        r'неможливо\s+(.+?)(?:\n|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    return None


# =============================================================================
# RAG Retrieval (like agent.py)
# =============================================================================

async def _retrieve_context(
    query: str,
    subject: str,
    grade: int,
    top_k: int = RETRIEVAL_TOP_K,
) -> str:
    """
    Retrieve context using hybrid RAG (like agent.py).

    Uses the existing hybrid_retriever which combines:
    - BM25 search (lexical)
    - Vector search (semantic)
    - RRF fusion
    """
    try:
        retriever = get_retriever()
        docs = await retriever.retrieve(
            query=query,
            subject=subject,
            grade=grade,
            top_k=top_k,
        )

        max_chars = _get_context_limit(subject)
        context, _ = format_context(docs, max_chars=max_chars, subject=subject)

        logger.debug(f"Retrieved {len(docs)} docs, context length: {len(context)}")
        return context

    except Exception as e:
        logger.error(f"RAG retrieval failed: {e}")
        return ""


# =============================================================================
# Main Validation Functions
# =============================================================================

async def validate_question(
    question_text: str,
    question_type: str,
    subject: str,
    grade: int,
    options: Optional[List[str]] = None,
    expected_index: Optional[int] = None,
    expected_indices: Optional[List[int]] = None,
    expected_answer: Optional[str] = None,
) -> CheckResult:
    """
    Unified validation with self-contained RAG (like agent.py).

    Flow:
    1. Retrieve context using hybrid RAG
    2. Solver solves question using subject-specific prompt
    3. Compare with expected answer
    4. Return CheckResult

    Args:
        question_text: The question text
        question_type: "single_choice" | "multiple_choice" | "open"
        subject: Subject name
        grade: Grade level
        options: List of options (MC only)
        expected_index: Expected correct answer index (single_choice only)
        expected_indices: Expected correct answer indices (multiple_choice only)
        expected_answer: Expected answer text (Open only)

    Returns:
        CheckResult with is_valid, reason, confidence, solver_answer, expected_answer
    """
    # Step 1: Build query and retrieve context (like agent.py)
    if question_type in ("single_choice", "multiple_choice"):
        # For MC: include options in query for better retrieval
        query = question_text
        if options:
            query = f"{question_text} {' '.join(options[:4])}"
    else:
        query = question_text

    context = await _retrieve_context(
        query=query,
        subject=subject,
        grade=grade,
    )

    # Step 2: Validate using appropriate method
    if question_type == "single_choice":
        return await _validate_mc(
            question_text=question_text,
            options=options or [],
            expected_index=expected_index,
            expected_indices=None,
            context=context,
            subject=subject,
            grade=grade,
            is_multiple=False,
        )
    elif question_type == "multiple_choice":
        return await _validate_mc(
            question_text=question_text,
            options=options or [],
            expected_index=None,
            expected_indices=expected_indices,
            context=context,
            subject=subject,
            grade=grade,
            is_multiple=True,
        )
    else:
        return await _validate_open(
            question_text=question_text,
            expected_answer=expected_answer or "",
            context=context,
            subject=subject,
            grade=grade,
        )


async def _validate_mc(
    question_text: str,
    options: List[str],
    expected_index: Optional[int],
    expected_indices: Optional[List[int]],
    context: str,
    subject: str,
    grade: int,
    is_multiple: bool = False,
) -> CheckResult:
    """
    Validate MC question using solver (agent.py style).

    1. Solver solves question using subject-specific expert prompt
    2. Extract answer letter(s) (A/B/C/D or A,C for multiple)
    3. Compare with expected index/indices
    4. Handle INVALID responses

    Args:
        is_multiple: True for multiple_choice (2-3 answers), False for single_choice
    """
    # Choose prompt based on question type
    if is_multiple:
        prompt = SOLVER_PROMPT_MULTIPLE.format(
            context=context if context else "Контекст не знайдено.",
            subject=subject,
            grade=grade,
            question=question_text,
            options=_format_options(options),
        )
    else:
        prompt_template = _get_solver_prompt(subject)
        prompt = prompt_template.format(
            context=context if context else "Контекст не знайдено.",
            subject=subject,
            grade=grade,
            question=question_text,
            options=_format_options(options),
        )

    # Solver generates text response (like agent.py)
    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        temperature=0.0,
        max_tokens=2000,
    )

    # Extract answer(s) from response
    solver_answer = _extract_answer(response, allow_multiple=is_multiple)

    # Handle INVALID - solver rejected the question
    if solver_answer == "INVALID":
        rejection_reason = _extract_rejection_reason(response)
        logger.info(
            f"MC Validation: solver=INVALID, reason={rejection_reason}"
        )
        return CheckResult(
            is_valid=False,
            reason=f"Solver rejected: {rejection_reason or 'question invalid'}",
            confidence=0.8,
            solver_answer="INVALID",
            expected_answer=_indices_to_letters(expected_indices) if is_multiple else _index_to_letter(expected_index or 0),
            is_rejected=True,
            rejection_reason=rejection_reason,
        )

    # Handle empty answer
    if not solver_answer:
        response_preview = response[:300] if response else "(empty)"
        logger.warning(f"MC Validation: could not extract answer from response: {response_preview}")
        return CheckResult(
            is_valid=False,
            reason="Solver failed to provide an answer",
            confidence=0.0,
            solver_answer="",
            expected_answer=_indices_to_letters(expected_indices) if is_multiple else _index_to_letter(expected_index or 0),
        )

    # Compare answers
    if is_multiple:
        # Multiple choice: compare sets of letters
        solver_set = set(solver_answer.split(","))
        expected_set = set(_index_to_letter(i) for i in (expected_indices or []))
        is_valid = solver_set == expected_set
        expected_str = _indices_to_letters(expected_indices or [])
    else:
        # Single choice: compare indices
        solver_idx = _letter_to_index(solver_answer)
        is_valid = solver_idx == (expected_index or 0)
        expected_str = _index_to_letter(expected_index or 0)

    if is_valid:
        reason = f"Solver agrees: {solver_answer}"
        confidence = 0.9
    else:
        reason = f"Solver chose {solver_answer}, expected {expected_str}"
        confidence = 0.3

    logger.info(
        f"MC Validation: solver={solver_answer}, expected={expected_str}, "
        f"valid={is_valid}, multiple={is_multiple}"
    )

    return CheckResult(
        is_valid=is_valid,
        reason=reason,
        confidence=confidence,
        solver_answer=solver_answer,
        expected_answer=expected_str,
    )


async def _validate_open(
    question_text: str,
    expected_answer: str,
    context: str,
    subject: str,
    grade: int,
) -> CheckResult:
    """
    Validate open question using solver (agent.py style).

    1. Solver generates an answer using text prompt
    2. Check for INVALID response
    3. LLM judge compares solver's answer with expected
    4. Match = Valid
    """
    client = get_llm_client()

    # Step 1: Solver generates answer
    solver_prompt = OPEN_SOLVER_PROMPT.format(
        subject=subject,
        grade=grade,
        context=context if context else "Контекст не знайдено.",
        question=question_text,
    )

    response = await client.generate(
        prompt=solver_prompt,
        temperature=0.0,
        max_tokens=2000,
    )

    # Check for INVALID first
    if re.search(r'\bINVALID\b', response, re.IGNORECASE):
        rejection_reason = _extract_rejection_reason(response)
        logger.info(f"Open Validation: solver=INVALID, reason={rejection_reason}")
        return CheckResult(
            is_valid=False,
            reason=f"Solver rejected: {rejection_reason or 'question invalid'}",
            confidence=0.8,
            solver_answer="INVALID",
            expected_answer=expected_answer,
            is_rejected=True,
            rejection_reason=rejection_reason,
        )

    # Extract answer from "Відповідь: ..." pattern
    match = re.search(r'Відповідь:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
    solver_answer = match.group(1).strip() if match else response.strip()[:200]

    if not solver_answer:
        return CheckResult(
            is_valid=False,
            reason="Solver failed to generate an answer",
            confidence=0.0,
            solver_answer="",
            expected_answer=expected_answer,
        )

    # Step 2: LLM judge compares answers
    compare_prompt = ANSWER_COMPARISON_PROMPT.format(
        question=question_text,
        expected=expected_answer,
        solver_answer=solver_answer,
    )

    compare_result = await generate_json_safe(
        prompt=compare_prompt,
        temperature=0.0,
        default={"match": False, "reason": "Comparison failed"}
    )

    is_match = compare_result.get("match", False)
    compare_reason = compare_result.get("reason", "")

    logger.info(
        f"Open Validation: solver='{solver_answer[:50]}...', expected='{expected_answer[:50]}...', "
        f"match={is_match}, reason={compare_reason}"
    )

    if is_match:
        return CheckResult(
            is_valid=True,
            reason=f"Answers match: {compare_reason}",
            confidence=0.9,
            solver_answer=solver_answer,
            expected_answer=expected_answer,
        )
    else:
        return CheckResult(
            is_valid=False,
            reason=f"Answers differ: {compare_reason}",
            confidence=0.3,
            solver_answer=solver_answer,
            expected_answer=expected_answer,
        )


# =============================================================================
# Backward Compatibility
# =============================================================================

async def check_mc_question(
    question_text: str,
    options: List[str],
    expected_index: int,
    context: str,
    subject: str,
    grade: int,
    use_support_scoring: bool = False,
) -> CheckResult:
    """DEPRECATED: Use validate_question() instead."""
    return await validate_question(
        question_text=question_text,
        question_type="single_choice",
        subject=subject,
        grade=grade,
        options=options,
        expected_index=expected_index,
    )


async def check_open_question(
    question_text: str,
    expected_answer: str,
    context: str,
    subject: str,
    grade: int,
) -> CheckResult:
    """DEPRECATED: Use validate_question() instead."""
    return await validate_question(
        question_text=question_text,
        question_type="open",
        subject=subject,
        grade=grade,
        expected_answer=expected_answer,
    )


async def check_question(
    question: Dict[str, Any],
    context: str,
    subject: str,
    grade: int,
) -> CheckResult:
    """DEPRECATED: Use validate_question() instead."""
    question_type = question.get("type", "open")
    question_text = question.get("question", "")

    return await validate_question(
        question_text=question_text,
        question_type=question_type,
        subject=subject,
        grade=grade,
        options=question.get("options"),
        expected_index=question.get("correct_answer_index"),
        expected_indices=question.get("correct_answer_indices"),
        expected_answer=question.get("explanation"),
    )
