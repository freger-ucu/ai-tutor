"""
Response Models

Pydantic models for API responses.
Based on: docs/api_flow_and_contracts.md

Note: All IDs are integers (from CSV data).
"""

from typing import Literal

from pydantic import BaseModel, Field

from app.models.domain import (
    Question,
    Solution,
)
from app.models.enums import Level


# =============================================================================
# RESPONSE SUB-MODELS (for proper serialization)
# =============================================================================


class ClassInfoResponse(BaseModel):
    """Class info for API response."""
    class_id: int
    class_number: int
    subject: str


class StudentSummaryResponse(BaseModel):
    """Student summary for API response."""
    student_id: int
    subject_level: Literal["weak", "medium", "strong"]
    average_subject_grade: float


class SkippedLessonResponse(BaseModel):
    """Skipped lesson for API response."""
    date: str
    topic: str


class ProblematicTopicResponse(BaseModel):
    """Problematic topic for API response."""
    topic: str
    average_score: float


# =============================================================================
# TEACHER RESPONSES
# =============================================================================


class TeacherClassesResponse(BaseModel):
    """EP1: Teacher's classes and subjects."""
    classes: list[ClassInfoResponse]


class StudentListResponse(BaseModel):
    """EP2: List of students in a class."""
    students: list[StudentSummaryResponse]


class TopicStatistic(BaseModel):
    """Statistics for a single topic."""
    topic: str
    count: int = Field(..., description="Number of students affected")
    avg_score: float | None = Field(None, description="Average score (for weak topics)")


class NotesStatistics(BaseModel):
    """Aggregated statistics for notes generation."""
    total_students: int = Field(..., description="Total students in the group")
    weak_topics: list[TopicStatistic] = Field(
        default_factory=list,
        description="Topics with low scores (< 6)"
    )
    skipped_topics: list[TopicStatistic] = Field(
        default_factory=list,
        description="Topics students missed"
    )


class NotesResponse(BaseModel):
    """EP3.1 & EP3.2: Generated notes."""
    title: str
    contents: str = Field(..., description="Lesson content in markdown")
    teacher_notes: str = Field(..., description="Tips for the teacher")
    sources: list[str] = Field(
        default_factory=list,
        description="RAG sources used (e.g., 'Істер, Розділ 2, с. 45')"
    )
    statistics: NotesStatistics | None = Field(
        None,
        description="Aggregated student gap statistics"
    )


class TestResponse(BaseModel):
    """EP4: Generated test pool."""
    title: str
    questions: list[Question]


class StudentDetailsResponse(BaseModel):
    """EP5: Detailed student data."""
    average_subject_grade: float = Field(..., ge=0, le=12)
    level: Literal["weak", "medium", "strong"]
    skipped_lessons: list[SkippedLessonResponse] = Field(default_factory=list)
    problematic_topics: list[ProblematicTopicResponse] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    """EP6: AI recommendation for a student."""
    feedback: str


class SolverResponse(BaseModel):
    """EP7: Solved single question with explanation."""
    question: str
    answer_explained: str


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


# =============================================================================
# INTERNAL RESPONSES (Testing only)
# =============================================================================


class AnswerKeyResponse(BaseModel):
    """Answer key with solutions for generated questions."""
    solutions: list[Solution]


class FullPipelineResponse(BaseModel):
    """Internal: Full pipeline integration test response."""
    notes: NotesResponse
    test: TestResponse
    answer_key: AnswerKeyResponse
