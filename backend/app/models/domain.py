"""
Domain Models

Core business objects for the AI Tutor system.
Based on: docs/api_flow_and_contracts.md

Note: All IDs are integers (from CSV data).
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import Difficulty, Level, QuestionType


class ClassInfo(BaseModel):
    """A class that a teacher teaches."""
    class_id: int
    class_number: int = Field(..., description="School grade: 8, 9, etc.")
    subject: str = Field(..., description="Subject name in Ukrainian")


class StudentSummary(BaseModel):
    """Summary info about a student in a class."""
    student_id: int
    subject_level: Level
    average_subject_grade: float = Field(..., ge=0, le=12)


class AnswerOption(BaseModel):
    """An answer option for single/multiple choice questions."""
    answer: str
    correct: bool


class Question(BaseModel):
    """A test question."""
    question: str
    type: QuestionType
    difficulty: Difficulty
    answer_options: Optional[list[AnswerOption]] = Field(
        None,
        description="Options for single/multiple choice. Null for open questions."
    )
    explanation: str
    topic: str
    subtopics: list[str] = Field(default_factory=list)
    focus: str = Field(default="", description="Specific aspect being tested")


class SkippedLesson(BaseModel):
    """A lesson that a student missed."""
    date: str = Field(..., description="ISO date: YYYY-MM-DD")
    topic: str


class ProblematicTopic(BaseModel):
    """A topic where student struggles."""
    topic: str
    average_score: float = Field(..., ge=0, le=12)


class QuestionResult(BaseModel):
    """Result of a single question in a completed test."""
    question: str
    answer: str
    correct: bool
    topic: str
    subtopics: list[str] = Field(default_factory=list)
    focus: str = Field(default="", description="Specific aspect being tested")


# =============================================================================
# Clustering Models (T5)
# =============================================================================


class StudentCluster(BaseModel):
    """A cluster of students with similar performance."""
    cluster_type: Level
    student_ids: list[int] = Field(default_factory=list)
    avg_score: float = Field(..., ge=0, le=12)
    score_range: tuple[float, float] = Field(..., description="(min, max) scores")


class ClusterAssignment(BaseModel):
    """Assignment of a single student to a cluster."""
    student_id: int
    cluster_type: Level
    avg_score: float = Field(..., ge=0, le=12)
    percentile: float = Field(..., ge=0, le=100)


class ClusterDistribution(BaseModel):
    """Distribution of students across clusters."""
    weak_count: int = 0
    medium_count: int = 0
    strong_count: int = 0
    weak_percentage: float = 0.0
    medium_percentage: float = 0.0
    strong_percentage: float = 0.0
    total_count: int = 0
