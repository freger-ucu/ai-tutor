"""
Shared Validation Prompts

Prompts used by multiple components for answer validation and support scoring.
Used by: question_checker.py, unified_generate.py
"""

# =============================================================================
# Support Scoring Prompt
# Used by: question_checker.py, (formerly flows/solver.py)
# =============================================================================

SUPPORT_SCORING_PROMPT = """Оціни, наскільки добре кожен варіант відповіді підтверджується контекстом.

Питання: {stem}

Варіанти:
0) {option_0}
1) {option_1}
2) {option_2}
3) {option_3}

Контекст:
{context}

Для кожного варіанту вкажи оцінку підтримки від 0 до 10, де:
- 0 = контекст суперечить або не містить інформації
- 5 = часткове підтвердження
- 10 = пряме підтвердження з контексту

Формат відповіді (JSON):
{{"scores": {{"0": 0, "1": 0, "2": 0, "3": 0}}, "best": 0, "reasoning": "..."}}

Тільки JSON:"""


# =============================================================================
# Verification Prompt
# Used by: unified_generate.py (verify loop for answer verification)
# =============================================================================

VERIFY_PROMPT = """Перевір, чи відповідь підтверджується контекстом.

Питання: {question}
Вибрана відповідь: {answer} ({answer_text})

Контекст:
{context}

Оціни:
1. Чи контекст містить пряме підтвердження відповіді?
2. Чи є суперечності?
3. Які терміни/факти могли б допомогти, але відсутні?

Формат відповіді (JSON):
{{"supported": true/false, "confidence": 0-10, "missing_terms": ["термін1", "термін2"], "reasoning": "..."}}

Тільки JSON:"""
