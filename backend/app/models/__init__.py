"""
Models Package

Pydantic models for the AI Tutor system.
Based on: docs/api_flow_and_contracts.md

Modules:
- enums: Level, Difficulty, QuestionType
- domain: Core business objects
- requests: API request validation
- responses: API response serialization
- state: LangGraph workflow states (TODO)
"""

# =============================================================================
# ENUMS
# =============================================================================
from app.models.enums import (
    Difficulty,
    Level,
    QuestionType,
)

# =============================================================================
# DOMAIN MODELS
# =============================================================================
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

# =============================================================================
# REQUEST MODELS
# =============================================================================
from app.models.requests import (
    CheckOpenQuestionRequest,
    FullPipelineRequest,
    GenerateIndividualNotesRequest,
    GenerateLevelNotesRequest,
    GenerateTestRequest,
    GetStudentListRequest,
    SolverRequest,
    StudentDetailsRequest,
    StudentRecommendationRequest,
    TestFeedbackRequest,
)

# =============================================================================
# RESPONSE MODELS
# =============================================================================
from app.models.responses import (
    AnswerKeyResponse,
    ClassInfoResponse,
    ErrorResponse,
    FullPipelineResponse,
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

# =============================================================================
# STATE MODELS (TODO: defined later)
# =============================================================================
# States will be imported here when LangGraph is implemented

# =============================================================================
# __all__
# =============================================================================
__all__ = [
    # Enums
    "Level",
    "Difficulty",
    "QuestionType",
    # Domain
    "ClassInfo",
    "StudentSummary",
    "AnswerOption",
    "Question",
    "SkippedLesson",
    "ProblematicTopic",
    "Solution",
    "QuestionResult",
    # Requests
    "GetStudentListRequest",
    "GenerateLevelNotesRequest",
    "GenerateIndividualNotesRequest",
    "GenerateTestRequest",
    "StudentDetailsRequest",
    "StudentRecommendationRequest",
    "SolverRequest",
    "CheckOpenQuestionRequest",
    "TestFeedbackRequest",
    "FullPipelineRequest",
    # Responses
    "ClassInfoResponse",
    "StudentSummaryResponse",
    "SkippedLessonResponse",
    "ProblematicTopicResponse",
    "TeacherClassesResponse",
    "StudentListResponse",
    "NotesResponse",
    "TestResponse",
    "StudentDetailsResponse",
    "RecommendationResponse",
    "SolverResponse",
    "StudentDataResponse",
    "OpenQuestionResultResponse",
    "TestFeedbackResponse",
    "HealthResponse",
    "ErrorResponse",
    "AnswerKeyResponse",
    "FullPipelineResponse",
]
