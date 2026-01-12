"""Tests for enums module."""

import pytest

from app.models.enums import Difficulty, Level, QuestionType


class TestLevel:
    """Tests for Level enum."""

    def test_level_values(self):
        """Level enum has correct values."""
        assert Level.WEAK.value == "weak"
        assert Level.MEDIUM.value == "medium"
        assert Level.STRONG.value == "strong"

    def test_level_count(self):
        """Level enum has exactly 3 values."""
        assert len(Level) == 3

    def test_level_from_string(self):
        """Level can be created from string."""
        assert Level("weak") == Level.WEAK
        assert Level("medium") == Level.MEDIUM
        assert Level("strong") == Level.STRONG

    def test_level_invalid_string(self):
        """Level raises error for invalid string."""
        with pytest.raises(ValueError):
            Level("invalid")

    def test_level_is_string(self):
        """Level serializes to string."""
        assert str(Level.WEAK) == "Level.WEAK"
        assert Level.WEAK.value == "weak"


class TestDifficulty:
    """Tests for Difficulty enum."""

    def test_difficulty_values(self):
        """Difficulty enum has correct values."""
        assert Difficulty.EASY.value == "easy"
        assert Difficulty.MEDIUM.value == "medium"
        assert Difficulty.DIFFICULT.value == "difficult"

    def test_difficulty_count(self):
        """Difficulty enum has exactly 3 values."""
        assert len(Difficulty) == 3

    def test_difficulty_from_string(self):
        """Difficulty can be created from string."""
        assert Difficulty("easy") == Difficulty.EASY
        assert Difficulty("medium") == Difficulty.MEDIUM
        assert Difficulty("difficult") == Difficulty.DIFFICULT

    def test_difficulty_invalid_string(self):
        """Difficulty raises error for invalid string."""
        with pytest.raises(ValueError):
            Difficulty("hard")  # Should be "difficult", not "hard"

    def test_difficulty_not_hard(self):
        """Difficulty does NOT have 'hard' value."""
        values = [d.value for d in Difficulty]
        assert "hard" not in values
        assert "difficult" in values


class TestQuestionType:
    """Tests for QuestionType enum."""

    def test_question_type_values(self):
        """QuestionType enum has correct values."""
        assert QuestionType.SINGLE_CHOICE.value == "single_choice"
        assert QuestionType.MULTIPLE_CHOICE.value == "multiple_choice"
        assert QuestionType.OPEN.value == "open"

    def test_question_type_count(self):
        """QuestionType enum has exactly 3 values."""
        assert len(QuestionType) == 3

    def test_question_type_from_string(self):
        """QuestionType can be created from string."""
        assert QuestionType("single_choice") == QuestionType.SINGLE_CHOICE
        assert QuestionType("multiple_choice") == QuestionType.MULTIPLE_CHOICE
        assert QuestionType("open") == QuestionType.OPEN

    def test_question_type_invalid(self):
        """QuestionType raises error for invalid string."""
        with pytest.raises(ValueError):
            QuestionType("essay")
