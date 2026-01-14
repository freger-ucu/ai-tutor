"""
Request Models

Pydantic models for validating incoming API requests.
Based on: docs/api_flow_and_contracts.md

Note: All IDs are integers (from CSV data).
"""

from pydantic import BaseModel, Field

from app.models.domain import QuestionResult
from app.models.enums import Level


# =============================================================================
# TEACHER REQUESTS
# =============================================================================


class GetStudentListRequest(BaseModel):
    """EP2: Get list of students in a class."""
    class_id: int
    teacher_id: int
    subject: str = Field(..., description="Subject name in Ukrainian")


class GenerateLevelNotesRequest(BaseModel):
    """EP3.1: Generate notes for students by level."""
    class_id: int
    teacher_id: int
    subject: str
    level_list: list[Level] = Field(..., description="Levels to generate for")
    topic_definition: str = Field(..., description="Topic description text")


class GenerateIndividualNotesRequest(BaseModel):
    """EP3.2: Generate notes for specific students."""
    class_id: int
    teacher_id: int
    subject: str
    student_list: list[int] = Field(..., description="Student IDs")
    topic_definition: str = Field(..., description="Topic description text")


class GenerateTestRequest(BaseModel):
    """EP4: Generate test pool."""
    class_id: int
    teacher_id: int
    subject: str
    topic_definition: str = Field(..., description="Topic description text")
    easy_count: int = Field(default=1, ge=0, le=20, description="Number of easy questions")
    medium_count: int = Field(default=1, ge=0, le=20, description="Number of medium questions")
    hard_count: int = Field(default=1, ge=0, le=20, description="Number of hard questions")


class StudentDetailsRequest(BaseModel):
    """EP5: Get detailed student data."""
    class_id: int
    subject: str
    teacher_id: int
    student_id: int


class StudentRecommendationRequest(BaseModel):
    """EP6: Get AI recommendation for a student."""
    student_id: int
    subject: str = Field(..., description="Subject name in Ukrainian")


# =============================================================================
# STUDENT REQUESTS
# =============================================================================


class CheckOpenQuestionRequest(BaseModel):
    """EP9: Check open question answer."""
    student_id: int
    subject: str
    topic: str
    subtopics: list[str] = Field(default_factory=list)
    question: str
    answer: str


class TestFeedbackRequest(BaseModel):
    """EP10: Get feedback after completing test."""
    student_id: int
    teacher_id: int
    subject: str
    questions: list[QuestionResult]


# =============================================================================
# INTERNAL REQUESTS (Testing only)
# =============================================================================


class FullPipelineRequest(BaseModel):
    """Internal: Full pipeline integration test request."""
    class_id: int
    teacher_id: int
    subject: str = Field(..., description="Subject name in Ukrainian")
    topic_definition: str = Field(..., description="Topic description text")
