"""
Student API Endpoints (T6)

Handles student-facing test flow:
- Get test exercises (without answers)
- Submit answers
- View results
- View personalized summary

All endpoints return MOCK data - will be connected to real services later.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


# =============================================================================
# Request/Response Models (for stubs)
# =============================================================================


class StudentAnswer(BaseModel):
    """A single answer from student."""
    exercise_id: str
    answer: str
    time_spent_seconds: Optional[int] = None


class SubmitAnswersRequest(BaseModel):
    """Request to submit test answers."""
    student_id: int
    test_id: str
    answers: list[StudentAnswer]


class SubmitAnswersResponse(BaseModel):
    """Response after submitting answers."""
    submission_id: str
    status: str = "received"


class ExerciseForStudent(BaseModel):
    """Exercise as shown to student (no correct answer)."""
    id: str
    question: str
    type: str
    difficulty: str
    options: Optional[list[str]] = None  # For multiple choice


class StudentTestResponse(BaseModel):
    """Test exercises for student."""
    test_id: str
    exercises: list[ExerciseForStudent]
    time_limit_minutes: Optional[int] = None


class ErrorPattern(BaseModel):
    """An error pattern identified in student's answers."""
    pattern_type: str
    description: str
    frequency: int


class StudentResultResponse(BaseModel):
    """Student's test result."""
    score: float
    percentage: float
    correct_count: int
    total_count: int
    correct_subtopics: list[str]
    failed_subtopics: list[str]
    error_patterns: list[ErrorPattern]
    class_percentile: float


class StudentSummaryResponse(BaseModel):
    """Personalized summary for student after test."""
    result_section: dict
    prerequisites_review: Optional[dict] = None
    mistakes_analysis: list[dict]
    practice_exercises: list[dict]
    recommendations: str


# =============================================================================
# Mock Data Generators
# =============================================================================


def _generate_mock_exercises(test_id: str) -> list[ExerciseForStudent]:
    """Generate mock exercises for a test."""
    exercises = [
        ExerciseForStudent(
            id="ex_001",
            question="Розв'яжіть рівняння: x² - 5x + 6 = 0",
            type="single_choice",
            difficulty="easy",
            options=["x = 2, x = 3", "x = -2, x = -3", "x = 1, x = 6", "x = -1, x = -6"]
        ),
        ExerciseForStudent(
            id="ex_002",
            question="Знайдіть дискримінант рівняння: 2x² + 3x - 5 = 0",
            type="single_choice",
            difficulty="easy",
            options=["49", "41", "-31", "9"]
        ),
        ExerciseForStudent(
            id="ex_003",
            question="Яка формула дискримінанта квадратного рівняння ax² + bx + c = 0?",
            type="single_choice",
            difficulty="easy",
            options=["D = b² - 4ac", "D = b² + 4ac", "D = 4ac - b²", "D = 2ac - b"]
        ),
        ExerciseForStudent(
            id="ex_004",
            question="Розв'яжіть рівняння: x² - 9 = 0",
            type="open",
            difficulty="easy"
        ),
        ExerciseForStudent(
            id="ex_005",
            question="Скільки коренів має рівняння, якщо D > 0?",
            type="single_choice",
            difficulty="medium",
            options=["2", "1", "0", "Безліч"]
        ),
        ExerciseForStudent(
            id="ex_006",
            question="Розв'яжіть рівняння: 3x² - 12x = 0",
            type="open",
            difficulty="medium"
        ),
        ExerciseForStudent(
            id="ex_007",
            question="Знайдіть суму коренів рівняння x² - 7x + 12 = 0",
            type="open",
            difficulty="medium"
        ),
        ExerciseForStudent(
            id="ex_008",
            question="Складіть квадратне рівняння з коренями x₁ = 2 та x₂ = 5",
            type="open",
            difficulty="difficult"
        ),
        ExerciseForStudent(
            id="ex_009",
            question="При яких значеннях k рівняння x² + kx + 4 = 0 має рівні корені?",
            type="open",
            difficulty="difficult"
        ),
        ExerciseForStudent(
            id="ex_010",
            question="Розв'яжіть систему: x + y = 5, xy = 6",
            type="open",
            difficulty="difficult"
        ),
    ]
    return exercises


def _generate_mock_result(student_id: int, test_id: str) -> StudentResultResponse:
    """Generate mock test result."""
    return StudentResultResponse(
        score=75.0,
        percentage=75.0,
        correct_count=8,
        total_count=10,
        correct_subtopics=["Дискримінант", "Формула коренів", "Теорема Вієта"],
        failed_subtopics=["Параметричні рівняння", "Системи з квадратними рівняннями"],
        error_patterns=[
            ErrorPattern(
                pattern_type="calculation",
                description="Помилки в обчисленні дискримінанта",
                frequency=2
            ),
            ErrorPattern(
                pattern_type="concept",
                description="Плутанина з кількістю коренів",
                frequency=1
            )
        ],
        class_percentile=65.0
    )


def _generate_mock_summary(student_id: int, test_id: str) -> StudentSummaryResponse:
    """Generate mock personalized summary."""
    return StudentSummaryResponse(
        result_section={
            "score": 75,
            "percentage": 75,
            "message": "Гарний результат! Ти засвоїв основні поняття.",
            "comparison": "Краще за 65% класу"
        },
        prerequisites_review={
            "topic": "Розкладання на множники",
            "reason": "Потрібно для розв'язування рівнянь методом факторизації",
            "pages": "Підручник, стор. 45-48"
        },
        mistakes_analysis=[
            {
                "question": "При яких значеннях k рівняння має рівні корені?",
                "your_answer": "k = 2",
                "correct_answer": "k = ±4",
                "explanation": "Для рівних коренів D = 0, тобто k² - 16 = 0, k = ±4"
            },
            {
                "question": "Розв'яжіть систему x + y = 5, xy = 6",
                "your_answer": "x = 1, y = 4",
                "correct_answer": "x = 2, y = 3 або x = 3, y = 2",
                "explanation": "Корені квадратного рівняння t² - 5t + 6 = 0"
            }
        ],
        practice_exercises=[
            {
                "question": "При яких значеннях m рівняння x² - 4x + m = 0 має один корінь?",
                "answer": "m = 4"
            },
            {
                "question": "Знайдіть добуток коренів: x² + 3x - 10 = 0",
                "answer": "-10"
            }
        ],
        recommendations="Рекомендую повторити тему 'Дискримінант та його властивості'. "
                       "Зверни увагу на випадки D = 0. Спробуй додаткові вправи з параметрами."
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/{student_id}/test", response_model=StudentTestResponse)
async def get_student_test(
    student_id: int,
    test_id: str = Query(..., description="Test identifier")
) -> StudentTestResponse:
    """
    Get test exercises for a student.

    Returns exercises WITHOUT correct answers.
    """
    exercises = _generate_mock_exercises(test_id)

    return StudentTestResponse(
        test_id=test_id,
        exercises=exercises,
        time_limit_minutes=45
    )


@router.post("/submit", response_model=SubmitAnswersResponse)
async def submit_answers(request: SubmitAnswersRequest) -> SubmitAnswersResponse:
    """
    Submit test answers.

    Returns submission ID and status.
    Processing happens asynchronously.
    """
    submission_id = str(uuid.uuid4())

    return SubmitAnswersResponse(
        submission_id=submission_id,
        status="received"
    )


@router.get("/{student_id}/result/{test_id}", response_model=StudentResultResponse)
async def get_student_result(
    student_id: int,
    test_id: str
) -> StudentResultResponse:
    """
    Get test result for a student.

    Returns score, correct/failed subtopics, and error patterns.
    """
    return _generate_mock_result(student_id, test_id)


@router.get("/{student_id}/summary/{test_id}", response_model=StudentSummaryResponse)
async def get_student_summary(
    student_id: int,
    test_id: str
) -> StudentSummaryResponse:
    """
    Get personalized summary for a student after test.

    Includes:
    - Result overview
    - Prerequisites review (if needed)
    - Detailed mistakes analysis
    - Practice exercises
    - Recommendations
    """
    return _generate_mock_summary(student_id, test_id)
