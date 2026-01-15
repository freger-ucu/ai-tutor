"""
CPU-based validators (no LLM calls).

Fast validation for format, structure, and basic constraints.
Used as first-pass filtering before expensive LLM validation.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ValidationError:
    """Validation error with field and message."""

    field: str
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class ValidationResult:
    """Result of CPU validation."""

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def issues(self) -> List[str]:
        """Get all issues as string list (for compatibility)."""
        return [e.message for e in self.errors + self.warnings]


# =============================================================================
# Question Format Validators
# =============================================================================


def validate_question_format(
    question: Dict[str, Any],
    existing_questions: Optional[Set[str]] = None,
) -> ValidationResult:
    """
    Validate question format and structure (CPU only).

    Checks:
    - Required fields present
    - Field types correct
    - For MC: Has 4 options, exactly 1 correct
    - Not duplicate of existing questions

    Args:
        question: Question dict to validate
        existing_questions: Set of existing question texts for dedup

    Returns:
        ValidationResult with errors/warnings
    """
    errors = []
    warnings = []

    # Required fields for all questions (difficulty is assigned post-factum)
    required_fields = ["question", "type"]
    for field in required_fields:
        if field not in question:
            errors.append(ValidationError(field, f"Missing required field: {field}"))

    if errors:
        return ValidationResult(is_valid=False, errors=errors)

    question_text = question.get("question", "")
    question_type = question.get("type", "")
    difficulty = question.get("difficulty", "")

    # Validate difficulty (optional - assigned post-factum by classify_difficulty_node)
    if difficulty:
        valid_difficulties = {"easy", "medium", "hard"}
        if difficulty not in valid_difficulties:
            warnings.append(
                ValidationError(
                    "difficulty", f"Invalid difficulty: {difficulty}. Must be one of {valid_difficulties}", "warning"
                )
            )

    # Validate question type
    valid_types = {"multiple_choice", "single_choice", "open"}
    if question_type not in valid_types:
        errors.append(
            ValidationError(
                "type", f"Invalid type: {question_type}. Must be one of {valid_types}"
            )
        )

    # Type-specific validation
    if question_type in {"multiple_choice", "single_choice"}:
        mc_result = _validate_mc_question(question)
        errors.extend(mc_result.errors)
        warnings.extend(mc_result.warnings)
    elif question_type == "open":
        open_result = _validate_open_question(question)
        errors.extend(open_result.errors)
        warnings.extend(open_result.warnings)

    # Check for duplicates
    if existing_questions and question_text:
        normalized = _normalize_text(question_text)
        if normalized in existing_questions:
            errors.append(
                ValidationError("question", "Duplicate question detected")
            )

    # Check question length
    if len(question_text) < 10:
        errors.append(
            ValidationError("question", "Question text too short (< 10 chars)")
        )
    elif len(question_text) > 1000:
        warnings.append(
            ValidationError("question", "Question text very long (> 1000 chars)", "warning")
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _validate_mc_question(question: Dict[str, Any]) -> ValidationResult:
    """Validate multiple choice question specifics."""
    errors = []
    warnings = []

    options = question.get("options", [])
    question_type = question.get("type", "single_choice")
    correct_index = question.get("correct_answer_index")
    correct_indices = question.get("correct_answer_indices")  # For multiple_choice with multiple correct

    # Must have options
    if not options:
        errors.append(ValidationError("options", "Missing options for MC question"))
        return ValidationResult(is_valid=False, errors=errors)

    # Must have exactly 4 options
    if len(options) != 4:
        errors.append(
            ValidationError("options", f"MC question must have exactly 4 options, got {len(options)}")
        )

    # Validate correct answer(s) based on question type
    if question_type == "single_choice":
        # single_choice: exactly 1 correct answer via correct_answer_index
        if correct_index is None:
            errors.append(
                ValidationError("correct_answer_index", "Missing correct_answer_index for single_choice")
            )
        elif not isinstance(correct_index, int):
            errors.append(
                ValidationError("correct_answer_index", f"correct_answer_index must be int, got {type(correct_index)}")
            )
        elif correct_index < 0 or correct_index >= len(options):
            errors.append(
                ValidationError("correct_answer_index", f"correct_answer_index {correct_index} out of range [0, {len(options)-1}]")
            )
    elif question_type == "multiple_choice":
        # multiple_choice: 2-3 correct answers via correct_answer_indices (list)
        if correct_indices is not None:
            if not isinstance(correct_indices, list):
                errors.append(
                    ValidationError("correct_answer_indices", f"correct_answer_indices must be list, got {type(correct_indices)}")
                )
            elif len(correct_indices) < 2:
                errors.append(
                    ValidationError("correct_answer_indices", f"multiple_choice must have 2-3 correct answers, got {len(correct_indices)}")
                )
            elif len(correct_indices) > 3:
                errors.append(
                    ValidationError("correct_answer_indices", f"multiple_choice should have at most 3 correct answers, got {len(correct_indices)}")
                )
            else:
                # Validate each index
                for idx in correct_indices:
                    if not isinstance(idx, int) or idx < 0 or idx >= len(options):
                        errors.append(
                            ValidationError("correct_answer_indices", f"Invalid index {idx} in correct_answer_indices")
                        )
                        break
        else:
            errors.append(
                ValidationError("correct_answer_indices", "multiple_choice must have correct_answer_indices (list with 2-3 indices)")
            )

    # Check option quality
    for i, opt in enumerate(options):
        if not isinstance(opt, str):
            errors.append(
                ValidationError("options", f"Option {i} must be string, got {type(opt)}")
            )
        elif len(opt.strip()) < 1:
            errors.append(
                ValidationError("options", f"Option {i} is empty")
            )

    # Check for duplicate options
    option_texts = [_normalize_text(str(o)) for o in options]
    if len(option_texts) != len(set(option_texts)):
        warnings.append(
            ValidationError("options", "Duplicate options detected", "warning")
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _validate_open_question(question: Dict[str, Any]) -> ValidationResult:
    """Validate open-ended question specifics."""
    errors = []
    warnings = []

    # Accept either expected_answer or explanation as the answer field
    expected_answer = question.get("expected_answer") or question.get("explanation")

    # Should have some form of answer
    if not expected_answer:
        warnings.append(
            ValidationError("expected_answer", "Missing expected_answer/explanation for open question", "warning")
        )
    elif len(str(expected_answer).strip()) < 2:
        warnings.append(
            ValidationError("expected_answer", "expected_answer too short", "warning")
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# =============================================================================
# Notes Format Validators
# =============================================================================


def validate_notes_format(
    notes: Dict[str, Any],
    required_sections: Optional[List[str]] = None,
) -> ValidationResult:
    """
    Validate notes structure (CPU only).

    Args:
        notes: Notes dict to validate
        required_sections: List of required section keys

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    # Basic structure check
    if not isinstance(notes, dict):
        errors.append(ValidationError("notes", "Notes must be a dictionary"))
        return ValidationResult(is_valid=False, errors=errors)

    # Check for content
    content = notes.get("content") or notes.get("notes") or notes.get("text")
    if not content:
        errors.append(ValidationError("content", "Notes must have content"))

    # Check required sections
    if required_sections:
        for section in required_sections:
            if section not in notes:
                warnings.append(
                    ValidationError(section, f"Missing section: {section}", "warning")
                )

    # Check content length
    if content and len(str(content)) < 50:
        warnings.append(
            ValidationError("content", "Notes content seems too short", "warning")
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# =============================================================================
# Generic JSON Structure Validators
# =============================================================================


def validate_json_structure(
    data: Any,
    schema: Dict[str, Any],
) -> ValidationResult:
    """
    Validate JSON structure against a simple schema.

    Schema format:
    {
        "field_name": {"type": "str", "required": True},
        "nested": {"type": "dict", "fields": {...}},
        "items": {"type": "list", "item_type": "str"},
    }

    Args:
        data: Data to validate
        schema: Schema definition

    Returns:
        ValidationResult
    """
    errors = []
    warnings = []

    if not isinstance(data, dict):
        errors.append(ValidationError("root", f"Expected dict, got {type(data).__name__}"))
        return ValidationResult(is_valid=False, errors=errors)

    for field_name, field_schema in schema.items():
        field_type = field_schema.get("type", "any")
        required = field_schema.get("required", False)
        value = data.get(field_name)

        # Check required
        if required and value is None:
            errors.append(ValidationError(field_name, f"Required field missing: {field_name}"))
            continue

        if value is None:
            continue

        # Type validation
        type_error = _validate_type(value, field_type, field_name)
        if type_error:
            errors.append(type_error)

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def _validate_type(value: Any, expected_type: str, field_name: str) -> Optional[ValidationError]:
    """Validate value type."""
    type_map = {
        "str": str,
        "int": int,
        "float": (int, float),
        "bool": bool,
        "list": list,
        "dict": dict,
        "any": object,
    }

    expected = type_map.get(expected_type)
    if expected and not isinstance(value, expected):
        return ValidationError(
            field_name,
            f"Expected {expected_type}, got {type(value).__name__}",
        )
    return None


# =============================================================================
# Utility Functions
# =============================================================================


def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove extra whitespace)."""
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def validate_batch_questions(
    questions: List[Dict[str, Any]],
    existing_texts: Optional[Set[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Tuple[int, ValidationResult]]]:
    """
    Validate a batch of questions, returning valid ones and errors.

    Args:
        questions: List of question dicts
        existing_texts: Set of existing question texts for dedup

    Returns:
        Tuple of (valid_questions, list of (index, validation_result) for failures)
    """
    valid = []
    failures = []
    seen_texts: Set[str] = existing_texts.copy() if existing_texts else set()

    for i, q in enumerate(questions):
        result = validate_question_format(q, seen_texts)
        if result.is_valid:
            valid.append(q)
            # Add to seen for dedup within batch
            q_text = q.get("question", "")
            if q_text:
                seen_texts.add(_normalize_text(q_text))
        else:
            failures.append((i, result))

    return valid, failures


def validate_single_question(
    question: Dict[str, Any],
    existing_texts: Optional[Set[str]] = None,
) -> Tuple[bool, str]:
    """
    Validate a single question, returning (is_valid, reason).

    Args:
        question: Question dict to validate
        existing_texts: Set of existing question texts for dedup

    Returns:
        Tuple of (is_valid, failure_reason or empty string)
    """
    if not question:
        return False, "Empty question"

    result = validate_question_format(question, existing_texts)

    if result.is_valid:
        return True, ""
    else:
        # Combine all error messages
        reasons = [e.message for e in result.errors]
        return False, "; ".join(reasons)
