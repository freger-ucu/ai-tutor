"""Tests for domain models."""

import pytest
from pydantic import ValidationError

from app.models.domain import (
    AnswerOption,
    ClassInfo,
    ProblematicTopic,
    Question,
    QuestionResult,
    SkippedLesson,
    Solution,
    StudentSummary,
)
from app.models.enums import Difficulty, Level, QuestionType


class TestClassInfo:
    """Tests for ClassInfo model."""

    def test_valid_class_info(self):
        """ClassInfo accepts valid data."""
        info = ClassInfo(class_id=1, class_number=8, subject="Алгебра")
        assert info.class_id == 1
        assert info.class_number == 8
        assert info.subject == "Алгебра"

    def test_class_info_requires_all_fields(self):
        """ClassInfo requires all fields."""
        with pytest.raises(ValidationError):
            ClassInfo(class_id=1, class_number=8)  # missing subject

    def test_class_info_id_coerces_string(self):
        """ClassInfo class_id coerces string to int (Pydantic v2 behavior)."""
        # Pydantic v2 coerces "1" to 1 automatically
        info = ClassInfo(class_id="1", class_number=8, subject="Алгебра")
        assert info.class_id == 1
        assert isinstance(info.class_id, int)

    def test_class_info_id_rejects_invalid_string(self):
        """ClassInfo class_id rejects non-numeric string."""
        with pytest.raises(ValidationError):
            ClassInfo(class_id="abc", class_number=8, subject="Алгебра")

    def test_class_info_accepts_any_subject_string(self):
        """ClassInfo accepts any subject string (Ukrainian)."""
        info = ClassInfo(class_id=1, class_number=9, subject="Українська мова")
        assert info.subject == "Українська мова"

    def test_class_info_serialization(self):
        """ClassInfo serializes to dict correctly."""
        info = ClassInfo(class_id=1, class_number=8, subject="Алгебра")
        data = info.model_dump()
        assert data == {"class_id": 1, "class_number": 8, "subject": "Алгебра"}


class TestStudentSummary:
    """Tests for StudentSummary model."""

    def test_valid_student_summary(self):
        """StudentSummary accepts valid data."""
        summary = StudentSummary(
            student_id=102,
            subject_level=Level.STRONG,
            average_subject_grade=10.5
        )
        assert summary.student_id == 102
        assert summary.subject_level == Level.STRONG
        assert summary.average_subject_grade == 10.5

    def test_student_summary_level_as_string(self):
        """StudentSummary accepts level as string."""
        summary = StudentSummary(
            student_id=1,
            subject_level="weak",
            average_subject_grade=4.0
        )
        assert summary.subject_level == Level.WEAK

    def test_student_summary_grade_min_boundary(self):
        """StudentSummary accepts grade=0."""
        summary = StudentSummary(
            student_id=1,
            subject_level=Level.WEAK,
            average_subject_grade=0
        )
        assert summary.average_subject_grade == 0

    def test_student_summary_grade_max_boundary(self):
        """StudentSummary accepts grade=12."""
        summary = StudentSummary(
            student_id=1,
            subject_level=Level.STRONG,
            average_subject_grade=12
        )
        assert summary.average_subject_grade == 12

    def test_student_summary_grade_below_min(self):
        """StudentSummary rejects grade < 0."""
        with pytest.raises(ValidationError):
            StudentSummary(
                student_id=1,
                subject_level=Level.WEAK,
                average_subject_grade=-1
            )

    def test_student_summary_grade_above_max(self):
        """StudentSummary rejects grade > 12."""
        with pytest.raises(ValidationError):
            StudentSummary(
                student_id=1,
                subject_level=Level.STRONG,
                average_subject_grade=13
            )

    def test_student_summary_invalid_level(self):
        """StudentSummary rejects invalid level."""
        with pytest.raises(ValidationError):
            StudentSummary(
                student_id=1,
                subject_level="excellent",  # invalid
                average_subject_grade=10
            )


class TestAnswerOption:
    """Tests for AnswerOption model."""

    def test_valid_answer_option(self):
        """AnswerOption accepts valid data."""
        option = AnswerOption(answer="x = 2", correct=True)
        assert option.answer == "x = 2"
        assert option.correct is True

    def test_answer_option_false(self):
        """AnswerOption accepts correct=False."""
        option = AnswerOption(answer="x = 3", correct=False)
        assert option.correct is False

    def test_answer_option_empty_answer(self):
        """AnswerOption accepts empty string answer."""
        option = AnswerOption(answer="", correct=False)
        assert option.answer == ""

    def test_answer_option_unicode(self):
        """AnswerOption handles Ukrainian text."""
        option = AnswerOption(answer="Відповідь: так", correct=True)
        assert option.answer == "Відповідь: так"


class TestQuestion:
    """Tests for Question model."""

    def test_valid_single_choice_question(self):
        """Question accepts valid single choice data."""
        question = Question(
            question="2 + 2 = ?",
            type=QuestionType.SINGLE_CHOICE,
            difficulty=Difficulty.EASY,
            answer_options=[
                AnswerOption(answer="3", correct=False),
                AnswerOption(answer="4", correct=True),
                AnswerOption(answer="5", correct=False),
            ],
            explanation="Basic addition",
            topic="Arithmetic",
            subtopics=["addition"]
        )
        assert question.type == QuestionType.SINGLE_CHOICE
        assert len(question.answer_options) == 3

    def test_valid_open_question(self):
        """Question accepts open question with null answer_options."""
        question = Question(
            question="Explain quadratic equations",
            type=QuestionType.OPEN,
            difficulty=Difficulty.MEDIUM,
            answer_options=None,
            explanation="Should mention ax² + bx + c = 0",
            topic="Algebra",
            subtopics=[]
        )
        assert question.type == QuestionType.OPEN
        assert question.answer_options is None

    def test_question_type_as_string(self):
        """Question accepts type as string."""
        question = Question(
            question="Test",
            type="multiple_choice",
            difficulty="difficult",
            answer_options=[],
            explanation="Test",
            topic="Test"
        )
        assert question.type == QuestionType.MULTIPLE_CHOICE
        assert question.difficulty == Difficulty.DIFFICULT

    def test_question_default_subtopics(self):
        """Question has empty subtopics by default."""
        question = Question(
            question="Test",
            type=QuestionType.OPEN,
            difficulty=Difficulty.EASY,
            answer_options=None,
            explanation="Test",
            topic="Test"
        )
        assert question.subtopics == []

    def test_question_invalid_type(self):
        """Question rejects invalid type."""
        with pytest.raises(ValidationError):
            Question(
                question="Test",
                type="essay",  # invalid
                difficulty=Difficulty.EASY,
                answer_options=None,
                explanation="Test",
                topic="Test"
            )


class TestSkippedLesson:
    """Tests for SkippedLesson model."""

    def test_valid_skipped_lesson(self):
        """SkippedLesson accepts valid data."""
        lesson = SkippedLesson(date="2024-09-15", topic="Дискримінант")
        assert lesson.date == "2024-09-15"
        assert lesson.topic == "Дискримінант"

    def test_skipped_lesson_any_date_format(self):
        """SkippedLesson accepts any date string (no validation)."""
        lesson = SkippedLesson(date="15/09/2024", topic="Test")
        assert lesson.date == "15/09/2024"

    def test_skipped_lesson_empty_topic(self):
        """SkippedLesson accepts empty topic."""
        lesson = SkippedLesson(date="2024-09-15", topic="")
        assert lesson.topic == ""


class TestProblematicTopic:
    """Tests for ProblematicTopic model."""

    def test_valid_problematic_topic(self):
        """ProblematicTopic accepts valid data."""
        topic = ProblematicTopic(topic="Квадратні рівняння", average_score=4.5)
        assert topic.topic == "Квадратні рівняння"
        assert topic.average_score == 4.5

    def test_problematic_topic_score_boundaries(self):
        """ProblematicTopic enforces 0-12 score."""
        # Valid boundaries
        ProblematicTopic(topic="Test", average_score=0)
        ProblematicTopic(topic="Test", average_score=12)

        # Invalid
        with pytest.raises(ValidationError):
            ProblematicTopic(topic="Test", average_score=-1)
        with pytest.raises(ValidationError):
            ProblematicTopic(topic="Test", average_score=13)


class TestSolution:
    """Tests for Solution model."""

    def test_valid_solution(self):
        """Solution accepts valid data."""
        solution = Solution(
            question="Solve x² - 4 = 0",
            answer_explained="x² = 4, x = ±2\n\nAnswer: x = 2 or x = -2"
        )
        assert solution.question == "Solve x² - 4 = 0"
        assert "x = 2" in solution.answer_explained

    def test_solution_multiline(self):
        """Solution handles multiline text."""
        solution = Solution(
            question="Q",
            answer_explained="Line 1\nLine 2\nLine 3"
        )
        assert "\n" in solution.answer_explained


class TestQuestionResult:
    """Tests for QuestionResult model."""

    def test_valid_question_result(self):
        """QuestionResult accepts valid data."""
        result = QuestionResult(
            question="2 + 2 = ?",
            answer="4",
            correct=True,
            topic="Arithmetic",
            subtopics=["addition"]
        )
        assert result.correct is True
        assert result.subtopics == ["addition"]

    def test_question_result_incorrect(self):
        """QuestionResult handles incorrect answer."""
        result = QuestionResult(
            question="2 + 2 = ?",
            answer="5",
            correct=False,
            topic="Arithmetic"
        )
        assert result.correct is False

    def test_question_result_default_subtopics(self):
        """QuestionResult has empty subtopics by default."""
        result = QuestionResult(
            question="Q",
            answer="A",
            correct=True,
            topic="T"
        )
        assert result.subtopics == []

    def test_question_result_empty_answer(self):
        """QuestionResult accepts empty answer (student skipped)."""
        result = QuestionResult(
            question="Q",
            answer="",
            correct=False,
            topic="T"
        )
        assert result.answer == ""
