"""Tests for request models."""

import pytest
from pydantic import ValidationError

from app.models.requests import (
    CheckOpenQuestionRequest,
    GenerateIndividualNotesRequest,
    GenerateLevelNotesRequest,
    GenerateTestRequest,
    GetStudentListRequest,
    SolverRequest,
    StudentDetailsRequest,
    StudentRecommendationRequest,
    TestFeedbackRequest,
)
from app.models.domain import QuestionResult
from app.models.enums import Level


class TestGetStudentListRequest:
    """Tests for GetStudentListRequest (EP2)."""

    def test_valid_request(self):
        """GetStudentListRequest accepts valid data."""
        req = GetStudentListRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра"
        )
        assert req.class_id == 1
        assert req.teacher_id == 4
        assert req.subject == "Алгебра"

    def test_ids_coerce_string_to_int(self):
        """GetStudentListRequest coerces string IDs to int (Pydantic v2)."""
        req = GetStudentListRequest(
            class_id="1",  # string, coerced to int
            teacher_id=4,
            subject="Алгебра"
        )
        assert req.class_id == 1
        assert isinstance(req.class_id, int)

    def test_ids_reject_invalid_string(self):
        """GetStudentListRequest rejects non-numeric string IDs."""
        with pytest.raises(ValidationError):
            GetStudentListRequest(
                class_id="abc",  # invalid string
                teacher_id=4,
                subject="Алгебра"
            )

    def test_all_fields_required(self):
        """GetStudentListRequest requires all fields."""
        with pytest.raises(ValidationError):
            GetStudentListRequest(class_id=1, teacher_id=4)  # missing subject


class TestGenerateLevelNotesRequest:
    """Tests for GenerateLevelNotesRequest (EP3.1)."""

    def test_valid_request(self):
        """GenerateLevelNotesRequest accepts valid data."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=[Level.WEAK, Level.MEDIUM],
            topic_definition="Квадратні рівняння"
        )
        assert req.level_list == [Level.WEAK, Level.MEDIUM]
        assert req.topic_definition == "Квадратні рівняння"

    def test_level_list_as_strings(self):
        """GenerateLevelNotesRequest accepts levels as strings."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=["weak", "strong"],
            topic_definition="Test"
        )
        assert req.level_list == [Level.WEAK, Level.STRONG]

    def test_empty_level_list(self):
        """GenerateLevelNotesRequest accepts empty level list."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=[],
            topic_definition="Test"
        )
        assert req.level_list == []

    def test_single_level(self):
        """GenerateLevelNotesRequest accepts single level."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=[Level.WEAK],
            topic_definition="Test"
        )
        assert len(req.level_list) == 1

    def test_all_levels(self):
        """GenerateLevelNotesRequest accepts all three levels."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=[Level.WEAK, Level.MEDIUM, Level.STRONG],
            topic_definition="Test"
        )
        assert len(req.level_list) == 3

    def test_invalid_level(self):
        """GenerateLevelNotesRequest rejects invalid level."""
        with pytest.raises(ValidationError):
            GenerateLevelNotesRequest(
                class_id=1,
                teacher_id=4,
                subject="Алгебра",
                level_list=["excellent"],  # invalid
                topic_definition="Test"
            )

    def test_topic_definition_is_string(self):
        """GenerateLevelNotesRequest topic_definition is string, not object."""
        req = GenerateLevelNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            level_list=[Level.WEAK],
            topic_definition="Just a string description"
        )
        assert isinstance(req.topic_definition, str)


class TestGenerateIndividualNotesRequest:
    """Tests for GenerateIndividualNotesRequest (EP3.2)."""

    def test_valid_request(self):
        """GenerateIndividualNotesRequest accepts valid data."""
        req = GenerateIndividualNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            student_list=[5, 12, 18],
            topic_definition="Квадратні рівняння"
        )
        assert req.student_list == [5, 12, 18]

    def test_student_list_coerces_strings(self):
        """GenerateIndividualNotesRequest coerces string IDs to ints (Pydantic v2)."""
        req = GenerateIndividualNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            student_list=["5", "12"],  # strings coerced to ints
            topic_definition="Test"
        )
        assert req.student_list == [5, 12]

    def test_student_list_rejects_invalid_strings(self):
        """GenerateIndividualNotesRequest rejects non-numeric strings in list."""
        with pytest.raises(ValidationError):
            GenerateIndividualNotesRequest(
                class_id=1,
                teacher_id=4,
                subject="Алгебра",
                student_list=["abc", "def"],  # invalid strings
                topic_definition="Test"
            )

    def test_empty_student_list(self):
        """GenerateIndividualNotesRequest accepts empty student list."""
        req = GenerateIndividualNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            student_list=[],
            topic_definition="Test"
        )
        assert req.student_list == []

    def test_single_student(self):
        """GenerateIndividualNotesRequest accepts single student."""
        req = GenerateIndividualNotesRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            student_list=[102],
            topic_definition="Test"
        )
        assert req.student_list == [102]


class TestGenerateTestRequest:
    """Tests for GenerateTestRequest (EP4)."""

    def test_valid_request(self):
        """GenerateTestRequest accepts valid data."""
        req = GenerateTestRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            topic_definition="Квадратні рівняння та їх розв'язання"
        )
        assert req.class_id == 1
        assert req.topic_definition == "Квадратні рівняння та їх розв'язання"

    def test_long_topic_definition(self):
        """GenerateTestRequest accepts long topic definition."""
        long_def = "A" * 10000
        req = GenerateTestRequest(
            class_id=1,
            teacher_id=4,
            subject="Алгебра",
            topic_definition=long_def
        )
        assert len(req.topic_definition) == 10000


class TestStudentDetailsRequest:
    """Tests for StudentDetailsRequest (EP5)."""

    def test_valid_request(self):
        """StudentDetailsRequest accepts valid data."""
        req = StudentDetailsRequest(
            class_id=1,
            subject="Алгебра",
            teacher_id=4,
            student_id=102
        )
        assert req.student_id == 102

    def test_ids_coerce_string_to_int(self):
        """StudentDetailsRequest coerces string IDs to int (Pydantic v2)."""
        req = StudentDetailsRequest(
            class_id=1,
            subject="Алгебра",
            teacher_id=4,
            student_id="102"  # string coerced to int
        )
        assert req.student_id == 102
        assert isinstance(req.student_id, int)

    def test_ids_reject_invalid_string(self):
        """StudentDetailsRequest rejects non-numeric string IDs."""
        with pytest.raises(ValidationError):
            StudentDetailsRequest(
                class_id=1,
                subject="Алгебра",
                teacher_id=4,
                student_id="abc"  # invalid string
            )


class TestStudentRecommendationRequest:
    """Tests for StudentRecommendationRequest (EP6)."""

    def test_valid_request(self):
        """StudentRecommendationRequest accepts valid data."""
        req = StudentRecommendationRequest(student_id=102)
        assert req.student_id == 102

    def test_only_student_id_required(self):
        """StudentRecommendationRequest only needs student_id."""
        req = StudentRecommendationRequest(student_id=1)
        assert hasattr(req, 'student_id')


class TestSolverRequest:
    """Tests for SolverRequest (EP7)."""

    def test_valid_request(self):
        """SolverRequest accepts valid data."""
        req = SolverRequest(questions=["2 + 2 = ?", "Solve x² = 4"])
        assert len(req.questions) == 2

    def test_empty_questions(self):
        """SolverRequest accepts empty questions list."""
        req = SolverRequest(questions=[])
        assert req.questions == []

    def test_single_question(self):
        """SolverRequest accepts single question."""
        req = SolverRequest(questions=["What is 2 + 2?"])
        assert len(req.questions) == 1

    def test_questions_must_be_strings(self):
        """SolverRequest questions must be strings."""
        with pytest.raises(ValidationError):
            SolverRequest(questions=[1, 2, 3])  # ints, not strings

    def test_unicode_questions(self):
        """SolverRequest handles Ukrainian text."""
        req = SolverRequest(questions=["Розв'яжіть рівняння: x² - 4 = 0"])
        assert "Розв'яжіть" in req.questions[0]


class TestCheckOpenQuestionRequest:
    """Tests for CheckOpenQuestionRequest (EP9)."""

    def test_valid_request(self):
        """CheckOpenQuestionRequest accepts valid data."""
        req = CheckOpenQuestionRequest(
            student_id=102,
            subject="Алгебра",
            topic="Квадратні рівняння",
            subtopics=["дискримінант"],
            question="Коли рівняння не має розв'язків?",
            answer="Коли D < 0"
        )
        assert req.student_id == 102
        assert req.subtopics == ["дискримінант"]

    def test_empty_subtopics(self):
        """CheckOpenQuestionRequest accepts empty subtopics."""
        req = CheckOpenQuestionRequest(
            student_id=102,
            subject="Алгебра",
            topic="Test",
            subtopics=[],
            question="Q",
            answer="A"
        )
        assert req.subtopics == []

    def test_default_subtopics(self):
        """CheckOpenQuestionRequest has empty subtopics by default."""
        req = CheckOpenQuestionRequest(
            student_id=102,
            subject="Алгебра",
            topic="Test",
            question="Q",
            answer="A"
        )
        assert req.subtopics == []

    def test_empty_answer(self):
        """CheckOpenQuestionRequest accepts empty answer."""
        req = CheckOpenQuestionRequest(
            student_id=102,
            subject="Алгебра",
            topic="Test",
            question="Q",
            answer=""
        )
        assert req.answer == ""


class TestTestFeedbackRequest:
    """Tests for TestFeedbackRequest (EP10)."""

    def test_valid_request(self):
        """TestFeedbackRequest accepts valid data."""
        req = TestFeedbackRequest(
            student_id=102,
            teacher_id=4,
            subject="Алгебра",
            questions=[
                QuestionResult(
                    question="2 + 2 = ?",
                    answer="4",
                    correct=True,
                    topic="Arithmetic"
                ),
                QuestionResult(
                    question="3 + 3 = ?",
                    answer="5",
                    correct=False,
                    topic="Arithmetic"
                ),
            ]
        )
        assert len(req.questions) == 2
        assert req.questions[0].correct is True
        assert req.questions[1].correct is False

    def test_empty_questions(self):
        """TestFeedbackRequest accepts empty questions."""
        req = TestFeedbackRequest(
            student_id=102,
            teacher_id=4,
            subject="Алгебра",
            questions=[]
        )
        assert req.questions == []

    def test_many_questions(self):
        """TestFeedbackRequest handles many questions."""
        questions = [
            QuestionResult(question=f"Q{i}", answer=f"A{i}", correct=i % 2 == 0, topic="T")
            for i in range(100)
        ]
        req = TestFeedbackRequest(
            student_id=102,
            teacher_id=4,
            subject="Алгебра",
            questions=questions
        )
        assert len(req.questions) == 100
