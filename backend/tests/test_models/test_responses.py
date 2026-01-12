"""Tests for response models."""

import pytest
from pydantic import ValidationError

from app.models.responses import (
    ErrorResponse,
    HealthResponse,
    NotesResponse,
    OpenQuestionResultResponse,
    RecommendationResponse,
    SolverResponse,
    StudentDataResponse,
    StudentDetailsResponse,
    StudentListResponse,
    TeacherDataResponse,
    TestFeedbackResponse,
    TestResponse,
)
from app.models.domain import (
    AnswerOption,
    ClassInfo,
    ProblematicTopic,
    Question,
    SkippedLesson,
    Solution,
    StudentSummary,
)
from app.models.enums import Difficulty, Level, QuestionType


class TestTeacherDataResponse:
    """Tests for TeacherDataResponse (EP1)."""

    def test_valid_response(self):
        """TeacherDataResponse accepts valid data."""
        resp = TeacherDataResponse(
            classes=[
                ClassInfo(class_id=1, class_number=8, subject="Алгебра"),
                ClassInfo(class_id=2, class_number=9, subject="Геометрія"),
            ]
        )
        assert len(resp.classes) == 2

    def test_empty_classes(self):
        """TeacherDataResponse accepts empty classes list."""
        resp = TeacherDataResponse(classes=[])
        assert resp.classes == []

    def test_single_class(self):
        """TeacherDataResponse accepts single class."""
        resp = TeacherDataResponse(
            classes=[ClassInfo(class_id=1, class_number=8, subject="Алгебра")]
        )
        assert len(resp.classes) == 1

    def test_serialization(self):
        """TeacherDataResponse serializes correctly."""
        resp = TeacherDataResponse(
            classes=[ClassInfo(class_id=1, class_number=8, subject="Алгебра")]
        )
        data = resp.model_dump()
        assert data["classes"][0]["class_id"] == 1


class TestStudentListResponse:
    """Tests for StudentListResponse (EP2)."""

    def test_valid_response(self):
        """StudentListResponse accepts valid data."""
        resp = StudentListResponse(
            students=[
                StudentSummary(student_id=1, subject_level=Level.WEAK, average_subject_grade=4.0),
                StudentSummary(student_id=2, subject_level=Level.STRONG, average_subject_grade=11.0),
            ]
        )
        assert len(resp.students) == 2

    def test_empty_students(self):
        """StudentListResponse accepts empty students list."""
        resp = StudentListResponse(students=[])
        assert resp.students == []

    def test_many_students(self):
        """StudentListResponse handles many students."""
        students = [
            StudentSummary(student_id=i, subject_level=Level.MEDIUM, average_subject_grade=7.0)
            for i in range(100)
        ]
        resp = StudentListResponse(students=students)
        assert len(resp.students) == 100


class TestNotesResponse:
    """Tests for NotesResponse (EP3.1 & EP3.2)."""

    def test_valid_response(self):
        """NotesResponse accepts valid data."""
        resp = NotesResponse(
            title="Квадратні рівняння",
            contents="## Основні поняття\n\nКвадратне рівняння...",
            teacher_notes="Зверніть увагу на дискримінант"
        )
        assert resp.title == "Квадратні рівняння"
        assert "Основні поняття" in resp.contents

    def test_markdown_content(self):
        """NotesResponse handles markdown content."""
        markdown = """
# Header
## Subheader

- Point 1
- Point 2

```python
x = 1
```
"""
        resp = NotesResponse(
            title="Test",
            contents=markdown,
            teacher_notes="Notes"
        )
        assert "# Header" in resp.contents

    def test_empty_teacher_notes(self):
        """NotesResponse accepts empty teacher notes."""
        resp = NotesResponse(
            title="Test",
            contents="Content",
            teacher_notes=""
        )
        assert resp.teacher_notes == ""

    def test_very_long_content(self):
        """NotesResponse handles very long content."""
        long_content = "A" * 100000
        resp = NotesResponse(
            title="Test",
            contents=long_content,
            teacher_notes="Notes"
        )
        assert len(resp.contents) == 100000


class TestTestResponse:
    """Tests for TestResponse (EP4)."""

    def test_valid_response(self):
        """TestResponse accepts valid data."""
        resp = TestResponse(
            title="Тест: Квадратні рівняння",
            questions=[
                Question(
                    question="2 + 2 = ?",
                    type=QuestionType.SINGLE_CHOICE,
                    difficulty=Difficulty.EASY,
                    answer_options=[
                        AnswerOption(answer="4", correct=True),
                        AnswerOption(answer="5", correct=False),
                    ],
                    explanation="Basic math",
                    topic="Math"
                )
            ]
        )
        assert resp.title == "Тест: Квадратні рівняння"
        assert len(resp.questions) == 1

    def test_empty_questions(self):
        """TestResponse accepts empty questions."""
        resp = TestResponse(title="Empty Test", questions=[])
        assert resp.questions == []

    def test_mixed_question_types(self):
        """TestResponse handles mixed question types."""
        resp = TestResponse(
            title="Mixed Test",
            questions=[
                Question(
                    question="Q1",
                    type=QuestionType.SINGLE_CHOICE,
                    difficulty=Difficulty.EASY,
                    answer_options=[AnswerOption(answer="A", correct=True)],
                    explanation="E1",
                    topic="T"
                ),
                Question(
                    question="Q2",
                    type=QuestionType.OPEN,
                    difficulty=Difficulty.DIFFICULT,
                    answer_options=None,
                    explanation="E2",
                    topic="T"
                ),
            ]
        )
        assert resp.questions[0].type == QuestionType.SINGLE_CHOICE
        assert resp.questions[1].type == QuestionType.OPEN


class TestStudentDetailsResponse:
    """Tests for StudentDetailsResponse (EP5)."""

    def test_valid_response(self):
        """StudentDetailsResponse accepts valid data."""
        resp = StudentDetailsResponse(
            average_subject_grade=7.5,
            level=Level.MEDIUM,
            skipped_lessons=[
                SkippedLesson(date="2024-09-15", topic="Дискримінант")
            ],
            problematic_topics=[
                ProblematicTopic(topic="Квадратні рівняння", average_score=5.0)
            ]
        )
        assert resp.average_subject_grade == 7.5
        assert resp.level == Level.MEDIUM

    def test_empty_lists(self):
        """StudentDetailsResponse accepts empty lists."""
        resp = StudentDetailsResponse(
            average_subject_grade=10.0,
            level=Level.STRONG,
            skipped_lessons=[],
            problematic_topics=[]
        )
        assert resp.skipped_lessons == []
        assert resp.problematic_topics == []

    def test_default_empty_lists(self):
        """StudentDetailsResponse has empty lists by default."""
        resp = StudentDetailsResponse(
            average_subject_grade=10.0,
            level=Level.STRONG
        )
        assert resp.skipped_lessons == []
        assert resp.problematic_topics == []

    def test_grade_boundaries(self):
        """StudentDetailsResponse enforces grade boundaries."""
        # Valid
        StudentDetailsResponse(average_subject_grade=0, level=Level.WEAK)
        StudentDetailsResponse(average_subject_grade=12, level=Level.STRONG)

        # Invalid
        with pytest.raises(ValidationError):
            StudentDetailsResponse(average_subject_grade=-1, level=Level.WEAK)
        with pytest.raises(ValidationError):
            StudentDetailsResponse(average_subject_grade=13, level=Level.STRONG)


class TestRecommendationResponse:
    """Tests for RecommendationResponse (EP6)."""

    def test_valid_response(self):
        """RecommendationResponse accepts valid data."""
        resp = RecommendationResponse(
            feedback="Учень має прогалини в темі 'Дискримінант'..."
        )
        assert "прогалини" in resp.feedback

    def test_empty_feedback(self):
        """RecommendationResponse accepts empty feedback."""
        resp = RecommendationResponse(feedback="")
        assert resp.feedback == ""

    def test_long_feedback(self):
        """RecommendationResponse handles long feedback."""
        long_feedback = "Recommendation " * 1000
        resp = RecommendationResponse(feedback=long_feedback)
        assert len(resp.feedback) > 10000


class TestSolverResponse:
    """Tests for SolverResponse (EP7)."""

    def test_valid_response(self):
        """SolverResponse accepts valid data."""
        resp = SolverResponse(
            solutions=[
                Solution(question="2 + 2 = ?", answer_explained="2 + 2 = 4"),
                Solution(question="x² = 4", answer_explained="x = ±2"),
            ]
        )
        assert len(resp.solutions) == 2

    def test_empty_solutions(self):
        """SolverResponse accepts empty solutions."""
        resp = SolverResponse(solutions=[])
        assert resp.solutions == []


class TestStudentDataResponse:
    """Tests for StudentDataResponse (EP8)."""

    def test_valid_response(self):
        """StudentDataResponse accepts valid data."""
        resp = StudentDataResponse(
            class_id=1,
            class_number=8,
            subjects=["Алгебра", "Геометрія", "Українська мова"]
        )
        assert resp.class_id == 1
        assert len(resp.subjects) == 3

    def test_empty_subjects(self):
        """StudentDataResponse accepts empty subjects."""
        resp = StudentDataResponse(
            class_id=1,
            class_number=8,
            subjects=[]
        )
        assert resp.subjects == []

    def test_single_subject(self):
        """StudentDataResponse accepts single subject."""
        resp = StudentDataResponse(
            class_id=1,
            class_number=8,
            subjects=["Алгебра"]
        )
        assert len(resp.subjects) == 1


class TestOpenQuestionResultResponse:
    """Tests for OpenQuestionResultResponse (EP9)."""

    def test_correct_answer(self):
        """OpenQuestionResultResponse handles correct answer."""
        resp = OpenQuestionResultResponse(
            correct=True,
            feedback="Правильно!"
        )
        assert resp.correct is True

    def test_incorrect_answer(self):
        """OpenQuestionResultResponse handles incorrect answer."""
        resp = OpenQuestionResultResponse(
            correct=False,
            feedback="Неправильно. Правильна відповідь: ..."
        )
        assert resp.correct is False

    def test_empty_feedback(self):
        """OpenQuestionResultResponse accepts empty feedback."""
        resp = OpenQuestionResultResponse(correct=True, feedback="")
        assert resp.feedback == ""


class TestTestFeedbackResponse:
    """Tests for TestFeedbackResponse (EP10)."""

    def test_valid_response(self):
        """TestFeedbackResponse accepts valid data."""
        resp = TestFeedbackResponse(
            feedback="Результат: 7/10 правильних відповідей..."
        )
        assert "7/10" in resp.feedback

    def test_empty_feedback(self):
        """TestFeedbackResponse accepts empty feedback."""
        resp = TestFeedbackResponse(feedback="")
        assert resp.feedback == ""


class TestHealthResponse:
    """Tests for HealthResponse."""

    def test_default_values(self):
        """HealthResponse has correct defaults."""
        resp = HealthResponse()
        assert resp.status == "healthy"
        assert resp.version == "0.1.0"

    def test_custom_values(self):
        """HealthResponse accepts custom values."""
        resp = HealthResponse(status="degraded", version="1.0.0")
        assert resp.status == "degraded"
        assert resp.version == "1.0.0"


class TestErrorResponse:
    """Tests for ErrorResponse."""

    def test_valid_error(self):
        """ErrorResponse accepts valid data."""
        resp = ErrorResponse(
            error="NOT_FOUND",
            message="Student not found"
        )
        assert resp.error == "NOT_FOUND"
        assert resp.message == "Student not found"

    def test_error_codes(self):
        """ErrorResponse handles various error codes."""
        errors = ["NOT_FOUND", "VALIDATION_ERROR", "INTERNAL_ERROR", "UNAUTHORIZED"]
        for code in errors:
            resp = ErrorResponse(error=code, message="Test")
            assert resp.error == code
