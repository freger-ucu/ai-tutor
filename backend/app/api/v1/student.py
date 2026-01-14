"""
Student API Endpoints

Implements EP8-EP10 per architecture.md contracts.
"""

from fastapi import APIRouter, HTTPException

from app.models.requests import TestFeedbackRequest, CheckOpenQuestionRequest
from app.models.responses import (
    StudentDataResponse,
    SubjectLevelResponse,
    TestFeedbackResponse,
    OpenQuestionResultResponse,
)
from app.services.data_loader import get_data_loader
from app.graph.flows.check_answer import check_open_answer
from app.graph.flows.feedback import generate_test_feedback

router = APIRouter()


# =============================================================================
# EP8: Get Student Info
# =============================================================================


@router.get("/{student_id}", response_model=StudentDataResponse)
def get_student(student_id: int) -> StudentDataResponse:
    """
    EP8: Get student's class and subjects with performance levels.

    Returns 404 if student not found in data.
    """
    data_loader = get_data_loader()

    if not data_loader.student_exists(student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    info = data_loader.get_student_info(student_id)

    if info is None:
        raise HTTPException(status_code=404, detail="Student not found")

    # Get subjects with levels
    subjects_with_levels = data_loader._get_student_subjects_with_levels(student_id)

    return StudentDataResponse(
        class_id=info["class_id"],
        class_number=info["class_number"],
        subjects=[
            SubjectLevelResponse(subject=s["subject"], level=s["level"])
            for s in subjects_with_levels
        ],
    )


# =============================================================================
# EP10: Test Feedback
# =============================================================================


@router.post("/test-feedback", response_model=TestFeedbackResponse)
async def get_test_feedback(request: TestFeedbackRequest) -> TestFeedbackResponse:
    """
    EP10: Get AI-generated feedback after completing a test.

    Uses LangGraph flow to analyze results and generate constructive feedback.
    """
    # Convert request questions to dict format for LangGraph flow
    questions = [
        {
            "question": q.question,
            "topic": q.topic,
            "subtopics": q.subtopics,
            "correct": q.correct,
        }
        for q in request.questions
    ]

    # Use LangGraph flow
    result = await generate_test_feedback(
        student_id=request.student_id,
        subject=request.subject,
        questions=questions,
    )

    return TestFeedbackResponse(feedback=result.feedback)


# =============================================================================
# EP9: Check Open Question
# =============================================================================


@router.post("/check-open", response_model=OpenQuestionResultResponse)
async def check_open_endpoint(
    request: CheckOpenQuestionRequest
) -> OpenQuestionResultResponse:
    """
    EP9: Check a student's answer to an open-ended question.

    Uses LangGraph flow with RAG retrieval and LLM evaluation.
    """
    # Get student's grade from their info
    data_loader = get_data_loader()
    student_info = data_loader.get_student_info(request.student_id)

    if student_info is None:
        grade = 8
    else:
        grade = student_info["class_number"]

    # Use LangGraph flow
    result = await check_open_answer(
        student_id=request.student_id,
        subject=request.subject,
        grade=grade,
        topic=request.topic,
        subtopics=request.subtopics,
        question=request.question,
        student_answer=request.answer,
    )

    return OpenQuestionResultResponse(
        correct=result.is_correct,
        feedback=result.feedback,
    )
