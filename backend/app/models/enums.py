"""
Enums Module

Fixed choice values used throughout the application.
Based on: docs/api_flow_and_contracts.md
"""

from enum import Enum


class Level(str, Enum):
    """Student performance level based on percentiles."""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


class Difficulty(str, Enum):
    """Question difficulty level."""
    EASY = "easy"
    MEDIUM = "medium"
    DIFFICULT = "difficult"


class QuestionType(str, Enum):
    """Type of test question."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN = "open"
