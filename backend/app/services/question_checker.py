"""
Question Checker Service.

Validates generated questions by checking if they have correct answers.
- MC questions: Uses support scoring to validate answer correctness
- Open questions: Checks if question has a definite, evaluable answer

V3: Two validation levels for MC questions:
- Lightweight (1 LLM call): Fast, single prompt validation
- Support Scoring (1 LLM call): Scores each option's support from context
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from app.rag.utils.llm_client import get_llm_client, generate_json_safe
from app.utils.json_parser import parse_json_response
from app.prompts.open_validator import OPEN_VALIDATOR_PROMPT
# Import from shared prompts location (avoids circular import with solver.py)
from app.prompts.solver import SUPPORT_SCORING_PROMPT

logger = logging.getLogger(__name__)


def _parse_support_scores(response: str) -> Tuple[Dict[int, float], Optional[int]]:
    """Parse support scoring response.

    Returns:
        Tuple of (scores dict, suggested best option index)
    """
    try:
        data = parse_json_response(response, {}, "SupportScoring")
        scores = data.get("scores", {})
        best = data.get("best", None)

        # Normalize scores to int keys
        float_scores = {}
        for k, v in scores.items():
            try:
                idx = int(k)
                if 0 <= idx <= 3:
                    float_scores[idx] = float(v) if v else 0.0
            except (ValueError, TypeError):
                continue

        # Parse best
        if best is not None:
            try:
                best = int(best)
                if not (0 <= best <= 3):
                    best = None
            except (ValueError, TypeError):
                best = None

        return float_scores, best
    except Exception as e:
        logger.warning(f"Failed to parse support scores: {e}")
        return {}, None


@dataclass
class CheckResult:
    """Result of question validation."""
    is_valid: bool
    reason: str
    solver_answer: Optional[int] = None
    confidence: Optional[float] = None
    option_scores: Optional[Dict[int, float]] = None


async def check_mc_question(
    question_text: str,
    options: List[str],
    expected_index: int,
    context: str,
    subject: str,
    grade: int,
    use_support_scoring: bool = False,
) -> CheckResult:
    """
    Check if MC question has the correct answer.

    V3: Two validation levels:
    1. use_support_scoring=True: Support scoring (1 LLM call, medium accuracy)
    2. use_support_scoring=False: Single lightweight LLM call (fastest)

    Args:
        question_text: The question text
        options: List of answer options
        expected_index: Expected correct answer index (0-based)
        context: RAG context for solving
        subject: Subject name
        grade: Grade level
        use_support_scoring: If True, uses support scoring (middle-ground)

    Returns:
        CheckResult with is_valid, reason, and additional fields (solver_answer,
        confidence, option_scores)
    """
    if use_support_scoring:
        # V3: Support scoring - middle-ground validation (1 LLM call)
        # Scores how well each option is supported by context
        client = get_llm_client()

        # Build prompt with all options
        prompt = SUPPORT_SCORING_PROMPT.format(
            stem=question_text,
            option_0=options[0] if len(options) > 0 else "",
            option_1=options[1] if len(options) > 1 else "",
            option_2=options[2] if len(options) > 2 else "",
            option_3=options[3] if len(options) > 3 else "",
            context=context[:3000] if context else "Контекст не знайдено.",
        )

        response = await client.generate(
            prompt=prompt,
            temperature=0.0,
            max_tokens=300,
        )

        scores, suggested_best = _parse_support_scores(response)
        expected_score = scores.get(expected_index, 0)

        logger.info(
            f"Support scoring: scores={scores}, suggested_best={suggested_best}, "
            f"expected={expected_index} (score={expected_score})"
        )

        # Validation criteria:
        # 1. If suggested best matches expected AND expected has decent score (>=5) -> valid
        # 2. If expected has high score (>=7) even if not suggested best -> valid
        # 3. Otherwise -> invalid

        if suggested_best == expected_index:
            return CheckResult(
                is_valid=True,
                reason=f"Support scoring agrees: answer {expected_index} (score={expected_score}/10)",
                solver_answer=suggested_best,
                confidence=expected_score / 10.0,
                option_scores=scores,
            )
        elif expected_score >= 7:
            # Expected answer has strong support even if not suggested best
            return CheckResult(
                is_valid=True,
                reason=f"Expected answer has strong support (score={expected_score}/10)",
                solver_answer=suggested_best,
                confidence=expected_score / 10.0,
                option_scores=scores,
            )
        else:
            # Check for ambiguity - multiple options with similar high scores
            high_scores = [i for i, s in scores.items() if s >= 6]
            if len(high_scores) > 1:
                return CheckResult(
                    is_valid=False,
                    reason=f"Ambiguous: multiple options have similar support {high_scores}",
                    solver_answer=suggested_best,
                    confidence=expected_score / 10.0,
                    option_scores=scores,
                )
            else:
                return CheckResult(
                    is_valid=False,
                    reason=f"Support scoring chose {suggested_best} (score={scores.get(suggested_best, 0)}/10), expected {expected_index} (score={expected_score}/10)",
                    solver_answer=suggested_best,
                    confidence=expected_score / 10.0,
                    option_scores=scores,
                )

    # Lightweight check using just the prompt (original behavior)
    from app.rag.nodes.unified_generate import SUBJECT_PROMPTS, DEFAULT_PROMPT, _format_options

    prompt_template = SUBJECT_PROMPTS.get(subject, DEFAULT_PROMPT)
    prompt = prompt_template.format(
        context=context if context else "Контекст не знайдено.",
        subject=subject,
        grade=grade,
        question=question_text,
        options=_format_options(options),
    )

    result = await generate_json_safe(
        prompt=prompt,
        temperature=0.0,
        default={"answer": 0, "analysis": "Generation failed"},
    )

    solver_answer = result.get("answer", result.get("answer_index", 0))

    # Validate solver_answer
    if not isinstance(solver_answer, int) or solver_answer < 0 or solver_answer >= len(options):
        solver_answer = 0

    if solver_answer == expected_index:
        return CheckResult(
            is_valid=True,
            reason=f"Solver agreed (answer={solver_answer})",
            solver_answer=solver_answer,
        )
    else:
        return CheckResult(
            is_valid=False,
            reason=f"Solver chose {solver_answer}, expected {expected_index}",
            solver_answer=solver_answer,
        )


async def check_open_question(
    question_text: str,
    expected_answer: str,
    context: str,
    subject: str,
    grade: int,
) -> CheckResult:
    """
    Check if open question has a definite, evaluable answer.

    Args:
        question_text: The question text
        expected_answer: Expected answer/explanation
        context: RAG context for validation
        subject: Subject name
        grade: Grade level

    Returns:
        CheckResult with is_valid and reason
    """
    prompt = OPEN_VALIDATOR_PROMPT.format(
        subject=subject,
        grade=grade,
        question=question_text,
        expected_answer=expected_answer,
        context=context if context else "Контекст не знайдено.",
    )

    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        temperature=0.0,
        max_tokens=500,
    )

    result = parse_json_response(
        response,
        fallback={"is_valid": False, "reason": "Failed to parse validation response"},
        context="OpenValidator",
    )

    is_valid = result.get("is_valid", False)
    reason = result.get("reason", "")

    if is_valid:
        return CheckResult(
            is_valid=True,
            reason=reason if reason else "Question has definite answer",
        )
    else:
        return CheckResult(
            is_valid=False,
            reason=reason if reason else "Question lacks definite answer",
        )


async def check_question(
    question: Dict[str, Any],
    context: str,
    subject: str,
    grade: int,
) -> CheckResult:
    """
    Check a question based on its type.

    Args:
        question: Question dict with type, question text, etc.
        context: RAG context for validation
        subject: Subject name
        grade: Grade level

    Returns:
        CheckResult with is_valid and reason
    """
    question_type = question.get("type", "open")
    question_text = question.get("question", "")

    if question_type == "single_choice":
        options = question.get("options", [])
        expected_index = question.get("correct_answer_index", 0)

        return await check_mc_question(
            question_text=question_text,
            options=options,
            expected_index=expected_index,
            context=context,
            subject=subject,
            grade=grade,
        )
    else:
        # Open question
        expected_answer = question.get("explanation", "")

        return await check_open_question(
            question_text=question_text,
            expected_answer=expected_answer,
            context=context,
            subject=subject,
            grade=grade,
        )
