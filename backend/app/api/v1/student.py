"""
Student API Endpoints

Implements EP8-EP10 per architecture.md contracts.
"""

from fastapi import APIRouter, HTTPException

from app.models.requests import TestFeedbackRequest, CheckOpenQuestionRequest
from app.models.responses import (
    StudentDataResponse,
    TestFeedbackResponse,
    OpenQuestionResultResponse,
)
from app.services.data_loader import get_data_loader
from app.rag.utils.llm_client import get_llm_client
from app.prompts.feedback import (
    FEEDBACK_SYSTEM_PROMPT,
    build_feedback_prompt,
)
from app.graph.flows.check_answer import check_open_answer

router = APIRouter()


# =============================================================================
# LLM Helper Functions
# =============================================================================


async def generate_test_feedback(
    subject: str,
    correct_count: int,
    total_count: int,
    incorrect_by_topic: dict[str, list[str]],
    correct_by_topic: dict[str, list[str]]
) -> str:
    """
    Generate AI feedback for test results.

    Uses LLM to create constructive feedback based on test performance.
    """
    prompt = build_feedback_prompt(
        subject=subject,
        correct_count=correct_count,
        total_count=total_count,
        incorrect_by_topic=incorrect_by_topic,
        correct_by_topic=correct_by_topic
    )

    full_prompt = f"{FEEDBACK_SYSTEM_PROMPT}\n\n{prompt}"

    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=800
    )

    return response


# =============================================================================
# EP8: Get Student Info
# =============================================================================


@router.get("/{student_id}", response_model=StudentDataResponse)
def get_student(student_id: int) -> StudentDataResponse:
    """
    EP8: Get student's class and subjects.

    Returns 404 if student not found in data.
    """
    data_loader = get_data_loader()

    if not data_loader.student_exists(student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    info = data_loader.get_student_info(student_id)

    if info is None:
        raise HTTPException(status_code=404, detail="Student not found")

    return StudentDataResponse(
        class_id=info["class_id"],
        class_number=info["class_number"],
        subjects=info["subjects"]
    )


# =============================================================================
# EP10: Test Feedback
# =============================================================================


@router.post("/test-feedback", response_model=TestFeedbackResponse)
async def get_test_feedback(request: TestFeedbackRequest) -> TestFeedbackResponse:
    """
    EP10: Get AI-generated feedback after completing a test.

    Analyzes test results and provides constructive feedback.
    """
    # Count correct answers
    correct_count = sum(1 for q in request.questions if q.correct)
    total_count = len(request.questions)

    # Group answers by topic/subtopics (per architecture.md specification)
    # Key: "topic" or "topic > subtopic1, subtopic2"
    incorrect_by_topic: dict[str, list[str]] = {}
    correct_by_topic: dict[str, list[str]] = {}

    for q in request.questions:
        # Build topic key including subtopics if present
        if q.subtopics:
            topic_key = f"{q.topic} > {', '.join(q.subtopics)}"
        else:
            topic_key = q.topic

        if q.correct:
            if topic_key not in correct_by_topic:
                correct_by_topic[topic_key] = []
            correct_by_topic[topic_key].append(q.question)
        else:
            if topic_key not in incorrect_by_topic:
                incorrect_by_topic[topic_key] = []
            incorrect_by_topic[topic_key].append(q.question)

    # Generate feedback using LLM
    feedback = await generate_test_feedback(
        subject=request.subject,
        correct_count=correct_count,
        total_count=total_count,
        incorrect_by_topic=incorrect_by_topic,
        correct_by_topic=correct_by_topic
    )

    return TestFeedbackResponse(feedback=feedback)


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
