"""Tests for response models."""

import pytest
from pydantic import ValidationError

from app.models.responses import (
    ClassInfoResponse,
    ErrorResponse,
    HealthResponse,
    NotesResponse,
    OpenQuestionResultResponse,
    ProblematicTopicResponse,
    RecommendationResponse,
    SkippedLessonResponse,
    SolverResponse,
    StudentDataResponse,
    StudentDetailsResponse,
    StudentListResponse,
    StudentSummaryResponse,
    TeacherClassesResponse,
    TestFeedbackResponse,
    TestResponse,
)
from app.models.domain import (
    AnswerOption,
    Question,
    Solution,
)
from app.models.enums import Difficulty, QuestionType


class TestTeacherClassesResponse:
    """Tests for TeacherClassesResponse (EP1)."""

    def test_valid_response(self):
        """TeacherClassesResponse accepts valid data."""
        resp = TeacherClassesResponse(
            classes=[
                ClassInfoResponse(class_id=1, class_number=8, subject="Алгебра"),
                ClassInfoResponse(class_id=2, class_number=9, subject="Геометрія"),
            ]
        )
        assert len(resp.classes) == 2

    def test_empty_classes(self):
        """TeacherClassesResponse accepts empty classes list."""
        resp = TeacherClassesResponse(classes=[])
        assert resp.classes == []

    def test_single_class(self):
        """TeacherClassesResponse accepts single class."""
        resp = TeacherClassesResponse(
            classes=[ClassInfoResponse(class_id=1, class_number=8, subject="Алгебра")]
        )
        assert len(resp.classes) == 1

    def test_serialization(self):
        """TeacherClassesResponse serializes correctly."""
        resp = TeacherClassesResponse(
            classes=[ClassInfoResponse(class_id=1, class_number=8, subject="Алгебра")]
        )
        data = resp.model_dump()
        assert data["classes"][0]["class_id"] == 1


class TestStudentListResponse:
    """Tests for StudentListResponse (EP2)."""

    def test_valid_response(self):
        """StudentListResponse accepts valid data."""
        resp = StudentListResponse(
            students=[
                StudentSummaryResponse(student_id=1, subject_level="weak", average_subject_grade=4.0),
                StudentSummaryResponse(student_id=2, subject_level="strong", average_subject_grade=11.0),
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
            StudentSummaryResponse(student_id=i, subject_level="medium", average_subject_grade=7.0)
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
            level="medium",
            skipped_lessons=[
                SkippedLessonResponse(date="2024-09-15", topic="Дискримінант")
            ],
            problematic_topics=[
                ProblematicTopicResponse(topic="Квадратні рівняння", average_score=5.0)
            ]
        )
        assert resp.average_subject_grade == 7.5
        assert resp.level == "medium"

    def test_empty_lists(self):
        """StudentDetailsResponse accepts empty lists."""
        resp = StudentDetailsResponse(
            average_subject_grade=10.0,
            level="strong",
            skipped_lessons=[],
            problematic_topics=[]
        )
        assert resp.skipped_lessons == []
        assert resp.problematic_topics == []

    def test_default_empty_lists(self):
        """StudentDetailsResponse has empty lists by default."""
        resp = StudentDetailsResponse(
            average_subject_grade=10.0,
            level="strong"
        )
        assert resp.skipped_lessons == []
        assert resp.problematic_topics == []

    def test_grade_boundaries(self):
        """StudentDetailsResponse enforces grade boundaries."""
        # Valid
        StudentDetailsResponse(average_subject_grade=0, level="weak")
        StudentDetailsResponse(average_subject_grade=12, level="strong")

        # Invalid
        with pytest.raises(ValidationError):
            StudentDetailsResponse(average_subject_grade=-1, level="weak")
        with pytest.raises(ValidationError):
            StudentDetailsResponse(average_subject_grade=13, level="strong")


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
        """SolverResponse accepts valid data with question and answer_explained."""
        resp = SolverResponse(
            question="Розв'яжіть рівняння: x² - 4 = 0",
            answer_explained="x² - 4 = 0 означає (x-2)(x+2) = 0, тому x = 2 або x = -2"
        )
        assert resp.question == "Розв'яжіть рівняння: x² - 4 = 0"
        assert "x = 2" in resp.answer_explained

    def test_requires_question(self):
        """SolverResponse requires question field."""
        with pytest.raises(ValidationError):
            SolverResponse(answer_explained="Test")

    def test_requires_answer_explained(self):
        """SolverResponse requires answer_explained field."""
        with pytest.raises(ValidationError):
            SolverResponse(question="Test")

    def test_handles_long_explanation(self):
        """SolverResponse handles long explanations."""
        long_explanation = "Step " * 1000
        resp = SolverResponse(question="Q", answer_explained=long_explanation)
        assert len(resp.answer_explained) > 4000


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
