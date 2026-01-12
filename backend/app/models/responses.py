"""
Response Models

Pydantic models for API responses.
Based on: docs/api_flow_and_contracts.md

Note: All IDs are integers (from CSV data).
"""

from pydantic import BaseModel, Field

from app.models.domain import (
    ClassInfo,
    ProblematicTopic,
    Question,
    SkippedLesson,
    Solution,
    StudentSummary,
)
from app.models.enums import Level


# =============================================================================
# TEACHER RESPONSES
# =============================================================================


class TeacherDataResponse(BaseModel):
    """EP1: Teacher's classes and subjects."""
    classes: list[ClassInfo]


class StudentListResponse(BaseModel):
    """EP2: List of students in a class."""
    students: list[StudentSummary]


class NotesResponse(BaseModel):
    """EP3.1 & EP3.2: Generated notes."""
    title: str
    contents: str = Field(..., description="Lesson content in markdown")
    teacher_notes: str = Field(..., description="Tips for the teacher")


class TestResponse(BaseModel):
    """EP4: Generated test pool."""
    title: str
    questions: list[Question]


class StudentDetailsResponse(BaseModel):
    """EP5: Detailed student data."""
    average_subject_grade: float = Field(..., ge=0, le=12)
    level: Level
    skipped_lessons: list[SkippedLesson] = Field(default_factory=list)
    problematic_topics: list[ProblematicTopic] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """EP6: AI recommendation for a student."""
    feedback: str


class SolverResponse(BaseModel):
    """EP7: Solved questions."""
    solutions: list[Solution]


# =============================================================================
# STUDENT RESPONSES
# =============================================================================


class StudentDataResponse(BaseModel):
    """EP8: Student's class and subjects."""
    class_id: int
    class_number: int
    subjects: list[str] = Field(..., description="Subject names in Ukrainian")


class OpenQuestionResultResponse(BaseModel):
    """EP9: Result of checking open question."""
    correct: bool
    feedback: str


class TestFeedbackResponse(BaseModel):
    """EP10: Feedback after completing test."""
    feedback: str


# =============================================================================
# COMMON RESPONSES
# =============================================================================


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
