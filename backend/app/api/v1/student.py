"""
Student API Endpoints

Implements EP8-EP10 per architecture.md contracts.
"""

from fastapi import APIRouter, HTTPException

import json

from app.models.requests import TestFeedbackRequest, CheckOpenQuestionRequest
from app.models.responses import (
    StudentDataResponse,
    TestFeedbackResponse,
    OpenQuestionResultResponse,
)
from app.services.data_loader import get_data_loader
from app.rag.utils.llm_client import get_llm_client
from app.rag.utils.hybrid_retriever import get_retriever, format_context
from app.prompts.feedback import (
    FEEDBACK_SYSTEM_PROMPT,
    build_feedback_prompt,
)
from app.prompts.evaluator import (
    EVALUATOR_SYSTEM_PROMPT,
    build_evaluator_prompt,
)

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


async def check_open_question(
    subject: str,
    grade: int,
    topic: str,
    subtopics: list[str],
    question: str,
    student_answer: str
) -> dict:
    """
    Check a student's open-ended answer using RAG + LLM.

    Retrieves relevant textbook content and evaluates the answer.

    Returns:
        dict with 'correct' (bool) and 'feedback' (str)
    """
    # RAG retrieval - use topic and question for better context
    retriever = get_retriever()
    query = f"{topic} {question}"
    docs = await retriever.retrieve(
        query=query,
        subject=subject,
        grade=grade
    )

    # Format context from retrieved documents
    context, _ = format_context(docs, max_chars=4000, subject=subject)

    # Build evaluation prompt
    prompt = build_evaluator_prompt(
        subject=subject,
        grade=grade,
        topic=topic,
        subtopics=subtopics,
        question=question,
        student_answer=student_answer,
        context=context
    )

    full_prompt = f"{EVALUATOR_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate evaluation
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.3,  # Lower temperature for more consistent evaluation
        max_tokens=600
    )

    # Parse JSON response
    try:
        # Try to extract JSON from the response
        response_text = response.strip()

        # Handle case where response contains text before/after JSON
        if "{" in response_text and "}" in response_text:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            json_str = response_text[start:end]
            result = json.loads(json_str)
        else:
            # Fallback: if no JSON found, parse as best effort
            result = {"correct": False, "feedback": response_text}

        # Ensure required fields exist
        if "correct" not in result:
            result["correct"] = False
        if "feedback" not in result:
            result["feedback"] = response_text

        return result

    except json.JSONDecodeError:
        # If JSON parsing fails, treat as incorrect with the full response as feedback
        return {
            "correct": False,
            "feedback": response
        }


@router.post("/check-open", response_model=OpenQuestionResultResponse)
async def check_open_endpoint(
    request: CheckOpenQuestionRequest
) -> OpenQuestionResultResponse:
    """
    EP9: Check a student's answer to an open-ended question.

    Uses RAG to retrieve relevant textbook content and LLM to evaluate.
    """
    # Get student's grade from their info
    data_loader = get_data_loader()
    student_info = data_loader.get_student_info(request.student_id)

    if student_info is None:
        # Default to grade 8 if student not found
        grade = 8
    else:
        grade = student_info["class_number"]

    # Check the answer
    result = await check_open_question(
        subject=request.subject,
        grade=grade,
        topic=request.topic,
        subtopics=request.subtopics,
        question=request.question,
        student_answer=request.answer
    )

    return OpenQuestionResultResponse(
        correct=result["correct"],
        feedback=result["feedback"]
    )
