"""
Internal API Routes

Testing-only endpoints for integration testing.
These endpoints should be excluded from production deployment
or protected behind admin authentication.
"""

import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from app.models.requests import FullPipelineRequest
from app.models.responses import (
    AnswerKeyResponse,
    FullPipelineResponse,
    NotesResponse,
    TestResponse,
)
from app.models.domain import AnswerOption, Question, Solution
from app.models.enums import QuestionType, Difficulty
from app.services.data_loader import DataLoader
from app.rag.utils.hybrid_retriever import HybridRetriever
from app.rag.utils.llm_client import get_llm_client
from app.prompts.notes_generator import (
    NOTES_SYSTEM_PROMPT,
    build_level_notes_prompt,
)
from app.prompts.test_generator import (
    TEST_GENERATOR_SYSTEM_PROMPT,
    build_test_generator_prompt,
)
from app.prompts.solver import SOLVER_SYSTEM_PROMPT, build_solver_prompt

router = APIRouter(prefix="/internal", tags=["internal"])

# Initialize shared services
data_loader = DataLoader()
retriever = HybridRetriever()


def extract_json(text: str) -> dict:
    """Extract JSON object from LLM response that may contain extra text."""
    # Try to parse the whole response first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r'\{[\s\S]*\}', text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Return empty dict if no JSON found
    return {}


async def generate_notes(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    gap_warnings: list[str],
) -> dict[str, Any]:
    """Generate notes using LLM (EP3 logic)."""
    prompt = build_level_notes_prompt(
        subject=subject,
        grade=grade,
        level="medium",  # Use medium level for general class notes
        topic_definition=topic_definition,
        context=context,
        gap_warnings=gap_warnings,
    )

    full_prompt = f"{NOTES_SYSTEM_PROMPT}\n\n{prompt}"
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=2000,
    )

    result = extract_json(response)
    return {
        "title": result.get("title", f"Урок: {topic_definition[:50]}"),
        "contents": result.get("contents", response),
        "teacher_notes": result.get("teacher_notes", ""),
    }


async def generate_test(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    num_questions: int = 30,
) -> dict[str, Any]:
    """Generate test pool using LLM (EP4 logic)."""
    prompt = build_test_generator_prompt(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context,
        num_questions=num_questions,
    )

    full_prompt = f"{TEST_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}"
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.8,
        max_tokens=4000,
    )

    result = extract_json(response)
    raw_questions = result.get("questions", [])

    # Convert raw questions to proper Question objects
    questions = []
    for q in raw_questions:
        # Parse question type
        q_type_str = q.get("type", "open").lower()
        q_type = QuestionType.multiple_choice if q_type_str == "multiple_choice" else QuestionType.open

        # Parse difficulty
        diff_str = q.get("difficulty", "medium").lower()
        if diff_str == "easy":
            difficulty = Difficulty.easy
        elif diff_str == "hard":
            difficulty = Difficulty.hard
        else:
            difficulty = Difficulty.medium

        # Parse answer options
        answer_options = []
        if q_type == QuestionType.multiple_choice:
            raw_options = q.get("options", [])
            correct_answer = q.get("correct_answer", "A")
            for i, opt in enumerate(raw_options[:4]):
                letter = chr(65 + i)  # A, B, C, D
                text = opt
                # Handle "A) text" format
                if isinstance(opt, str) and len(opt) > 2 and opt[1] in [')', '.', ':']:
                    text = opt[2:].strip()
                is_correct = (letter == correct_answer)
                answer_options.append(AnswerOption(answer=text, correct=is_correct))

        questions.append({
            "question": q.get("question", ""),
            "type": q_type.value,
            "difficulty": difficulty.value,
            "answer_options": [{"answer": ao.answer, "correct": ao.correct} for ao in answer_options],
            "explanation": q.get("explanation", ""),
            "topic": q.get("topic", ""),
            "subtopics": [],
        })

    return {
        "title": result.get("title", f"Тест: {topic_definition[:50]}"),
        "questions": questions,
    }


async def solve_question(
    subject: str,
    grade: int,
    question: str,
    context: str,
) -> dict[str, str]:
    """Solve a single question using LLM (EP7 logic)."""
    prompt = build_solver_prompt(
        subject=subject,
        grade=grade,
        question=question,
        context=context,
    )

    full_prompt = f"{SOLVER_SYSTEM_PROMPT}\n\n{prompt}"
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.3,
        max_tokens=1000,
    )

    return {
        "question": question,
        "answer_explained": response,
    }


@router.post("/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline_endpoint(request: FullPipelineRequest) -> FullPipelineResponse:
    """
    Full pipeline integration test endpoint.

    Exercises: Data + RAG + LLM integration.
    1. Gets class info and gap warnings
    2. Retrieves content via RAG
    3. Generates notes (EP3 logic)
    4. Generates test pool (EP4 logic)
    5. Solves each question (EP7 logic, called N times)

    WARNING: This is a testing-only endpoint.
    Should be excluded from production or protected.
    """
    # 1. Get class info
    class_info = data_loader.get_class_info(request.class_id)
    if not class_info:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    # 2. Get gap warnings for the whole class
    gap_warnings = data_loader.get_level_gap_warnings(
        class_id=request.class_id,
        subject=request.subject,
        level="all",  # Get warnings for all levels
    )

    # 3. RAG retrieval for topic
    retrieved_pages = await retriever.retrieve(
        query=request.topic_definition,
        subject=request.subject,
        grade=grade,
        top_k=5,
    )
    context = "\n\n---\n\n".join([
        f"[Сторінка {p.get('page_number', '?')}]\n{p.get('text', '')}"
        for p in retrieved_pages
    ])

    # 4. Generate notes (EP3 logic)
    notes_result = await generate_notes(
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
        context=context,
        gap_warnings=gap_warnings,
    )
    notes = NotesResponse(
        title=notes_result["title"],
        contents=notes_result["contents"],
        teacher_notes=notes_result["teacher_notes"],
    )

    # 5. Generate test pool (EP4 logic)
    test_result = await generate_test(
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
        context=context,
        num_questions=30,
    )

    # Convert to Question objects
    questions = []
    for q in test_result["questions"]:
        q_type = QuestionType(q["type"]) if q["type"] in ["multiple_choice", "open"] else QuestionType.open
        difficulty = Difficulty(q["difficulty"]) if q["difficulty"] in ["easy", "medium", "hard"] else Difficulty.medium

        answer_options = [
            AnswerOption(answer=ao["answer"], correct=ao["correct"])
            for ao in q.get("answer_options", [])
        ]

        questions.append(Question(
            question=q["question"],
            type=q_type,
            difficulty=difficulty,
            answer_options=answer_options,
            explanation=q.get("explanation", ""),
            topic=q.get("topic", ""),
            subtopics=q.get("subtopics", []),
        ))

    test = TestResponse(
        title=test_result["title"],
        questions=questions,
    )

    # 6. Solve each question (EP7 logic, called N times)
    solutions = []
    for q in questions:
        solution_result = await solve_question(
            subject=request.subject,
            grade=grade,
            question=q.question,
            context=context,
        )
        solutions.append(Solution(
            question=solution_result["question"],
            answer_explained=solution_result["answer_explained"],
        ))

    answer_key = AnswerKeyResponse(solutions=solutions)

    return FullPipelineResponse(
        notes=notes,
        test=test,
        answer_key=answer_key,
    )
