"""
Teacher API Endpoints

Implements EP1-EP7 per architecture.md contracts.
"""

import json
import logging
import re

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from app.models.requests import (
    GetStudentListRequest,
    StudentDetailsRequest,
    StudentRecommendationRequest,
    SolverRequest,
    GenerateLevelNotesRequest,
    GenerateIndividualNotesRequest,
    GenerateTestRequest,
)
from app.models.responses import (
    TeacherClassesResponse,
    StudentListResponse,
    StudentDetailsResponse,
    StudentSummaryResponse,
    SkippedLessonResponse,
    ProblematicTopicResponse,
    ClassInfoResponse,
    RecommendationResponse,
    SolverResponse,
    NotesResponse,
    NotesStatistics,
    TopicStatistic,
    TestResponse,
)
from app.models.domain import Question, AnswerOption
from app.models.enums import QuestionType, Difficulty
from app.services.data_loader import get_data_loader
from app.rag.utils.llm_client import get_llm_client
from app.rag.utils.hybrid_retriever import get_retriever, format_context
from app.prompts.recommendation import (
    RECOMMENDATION_SYSTEM_PROMPT,
    build_recommendation_prompt,
)
from app.prompts.solver import (
    SOLVER_SYSTEM_PROMPT,
    build_solver_prompt,
)
from app.prompts.notes_generator import (
    NOTES_SYSTEM_PROMPT,
    build_level_notes_prompt,
    build_individual_notes_prompt,
)

# NOTE: generate_test_pool is imported lazily in generate_test_endpoint()
# to avoid loading grpcio/langsmith at module import time (macOS mutex.cc issue)

router = APIRouter()


def _format_sources(references: list[dict]) -> list[str]:
    """
    Format RAG references into human-readable source strings.

    Args:
        references: List of dicts with 'book', 'section', 'topic', 'page'

    Returns:
        List of formatted source strings like "Істер, Розділ 2, с. 45"
    """
    sources = []
    for ref in references:
        book = ref.get("book", "")
        section = ref.get("section", "")
        page = ref.get("page", 0)

        if book and section:
            sources.append(f"{book}, {section}, с. {page}")
        elif book:
            sources.append(f"{book}, с. {page}")

    return sources


def _build_notes_statistics(aggregated_gaps: dict | None) -> NotesStatistics | None:
    """
    Convert aggregated_gaps dict to NotesStatistics model.

    Args:
        aggregated_gaps: Dict from aggregate_student_gaps()

    Returns:
        NotesStatistics model or None if no meaningful data
    """
    if not aggregated_gaps:
        return None

    raw_weak = aggregated_gaps.get("weak_topics", {})
    raw_skipped = aggregated_gaps.get("skipped_topics", {})

    # Return None if there's no actual data
    if not raw_weak and not raw_skipped:
        return None

    weak_topics = []
    for topic, info in raw_weak.items():
        # Clean topic name (strip whitespace/newlines)
        clean_topic = topic.strip()
        if not clean_topic:
            continue
        weak_topics.append(TopicStatistic(
            topic=clean_topic,
            count=info.get("count", 0),
            avg_score=info.get("avg_score")
        ))

    skipped_topics = []
    for topic, info in raw_skipped.items():
        # Clean topic name (strip whitespace/newlines)
        clean_topic = topic.strip()
        if not clean_topic:
            continue
        skipped_topics.append(TopicStatistic(
            topic=clean_topic,
            count=info.get("count", 0),
            avg_score=None
        ))

    # Return None if after cleaning there's nothing
    if not weak_topics and not skipped_topics:
        return None

    return NotesStatistics(
        total_students=aggregated_gaps.get("total_students", 0),
        weak_topics=weak_topics,
        skipped_topics=skipped_topics
    )


def _parse_notes_json(response: str, topic_definition: str) -> dict:
    """
    Parse JSON response from LLM for notes generation.

    Handles:
    - Clean JSON
    - JSON wrapped in ```json code blocks
    - Malformed JSON with unescaped newlines
    """
    response_text = response.strip()

    # Remove markdown code blocks if present
    if "```json" in response_text:
        response_text = response_text.split("```json", 1)[1]
        if "```" in response_text:
            response_text = response_text.split("```", 1)[0]
        response_text = response_text.strip()
    elif "```" in response_text:
        parts = response_text.split("```")
        if len(parts) >= 2:
            response_text = parts[1].strip()
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()

    # Try to parse as JSON
    if "{" in response_text and "}" in response_text:
        start = response_text.find("{")
        end = response_text.rfind("}") + 1
        json_str = response_text[start:end]

        # First try: direct parse
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Second try: use regex to extract fields (handles malformed JSON)
        try:
            title_match = re.search(r'"title"\s*:\s*"([^"]*)"', json_str)

            # For contents and teacher_notes, find the field and extract until next field or end
            contents_match = re.search(r'"contents"\s*:\s*"(.*?)",\s*"teacher_notes"', json_str, re.DOTALL)
            if not contents_match:
                contents_match = re.search(r'"contents"\s*:\s*"(.*?)"(?:,|\s*})', json_str, re.DOTALL)

            teacher_notes_match = re.search(r'"teacher_notes"\s*:\s*"(.*?)"(?:\s*}|$)', json_str, re.DOTALL)

            result = {}
            if title_match:
                result["title"] = title_match.group(1)
            if contents_match:
                # Unescape the content
                content = contents_match.group(1)
                content = content.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                result["contents"] = content
            if teacher_notes_match:
                notes = teacher_notes_match.group(1)
                notes = notes.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                result["teacher_notes"] = notes

            if result:
                # Ensure all required fields
                if "title" not in result:
                    result["title"] = f"Урок: {topic_definition[:50]}"
                if "contents" not in result:
                    result["contents"] = response_text
                if "teacher_notes" not in result:
                    result["teacher_notes"] = ""
                return result
        except Exception:
            pass

    # Fallback: return raw response as contents
    return {
        "title": f"Урок: {topic_definition[:50]}",
        "contents": response_text if response_text else response,
        "teacher_notes": ""
    }


# =============================================================================
# LLM Helper Functions
# =============================================================================


async def generate_recommendation(
    subject: str,
    average_grade: float,
    level: str,
    good_topics: list[str],
    bad_topics: list[str],
    missed_topics: list[str]
) -> str:
    """
    Generate AI recommendation for a student.

    Uses LLM to create personalized feedback based on student performance.
    """
    prompt = build_recommendation_prompt(
        subject=subject,
        average_grade=average_grade,
        level=level,
        good_topics=good_topics,
        bad_topics=bad_topics,
        missed_topics=missed_topics
    )

    full_prompt = f"{RECOMMENDATION_SYSTEM_PROMPT}\n\n{prompt}"

    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=800
    )

    return response


# =============================================================================
# EP1: Get Teacher Classes
# =============================================================================


@router.get("/{teacher_id}", response_model=TeacherClassesResponse)
def get_teacher(teacher_id: int) -> TeacherClassesResponse:
    """
    EP1: Get list of classes taught by a teacher.

    Returns 404 if teacher not found in data.
    """
    data_loader = get_data_loader()

    if not data_loader.teacher_exists(teacher_id):
        raise HTTPException(status_code=404, detail="Teacher not found")

    classes = data_loader.get_teacher_classes(teacher_id)

    return TeacherClassesResponse(
        classes=[
            ClassInfoResponse(
                class_id=c.class_id,
                class_number=c.class_number,
                subject=c.subject
            )
            for c in classes
        ]
    )


# =============================================================================
# EP2: Get Student List
# =============================================================================


@router.post("/students", response_model=StudentListResponse)
def get_students(request: GetStudentListRequest) -> StudentListResponse:
    """
    EP2: Get list of students in a class with their levels.

    Returns 404 if class/subject combination not found.
    """
    data_loader = get_data_loader()

    students = data_loader.get_class_students(
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    if not students:
        # Check if the class exists at all
        # If no students found, it could be invalid class/subject combination
        raise HTTPException(
            status_code=404,
            detail="No students found for this class/subject combination"
        )

    return StudentListResponse(
        students=[
            StudentSummaryResponse(
                student_id=s.student_id,
                subject_level=s.subject_level.value,
                average_subject_grade=s.average_subject_grade
            )
            for s in students
        ]
    )


# =============================================================================
# EP5: Get Student Details
# =============================================================================


@router.post("/student/details", response_model=StudentDetailsResponse)
def get_student_details(request: StudentDetailsRequest) -> StudentDetailsResponse:
    """
    EP5: Get detailed information about a specific student.

    Returns 404 if student not found in the class/subject.
    """
    data_loader = get_data_loader()

    details = data_loader.get_student_details(
        student_id=request.student_id,
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    if details is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found in this class/subject"
        )

    return StudentDetailsResponse(
        average_subject_grade=details["average_subject_grade"],
        level=details["level"].value,
        skipped_lessons=[
            SkippedLessonResponse(date=l.date, topic=l.topic)
            for l in details["skipped_lessons"]
        ],
        problematic_topics=[
            ProblematicTopicResponse(topic=t.topic, average_score=t.average_score)
            for t in details["problematic_topics"]
        ]
    )


# =============================================================================
# EP6: Get Student Recommendation
# =============================================================================


@router.post("/student/recommendation", response_model=RecommendationResponse)
async def get_student_recommendation(
    request: StudentRecommendationRequest
) -> RecommendationResponse:
    """
    EP6: Get AI-generated recommendation for a student.

    Returns personalized feedback based on student's performance in a subject.
    """
    data_loader = get_data_loader()

    # Get recommendation data
    rec_data = data_loader.get_student_recommendation_data(
        student_id=request.student_id,
        subject=request.subject
    )

    if rec_data is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found or does not have this subject"
        )

    # Generate recommendation using LLM
    feedback = await generate_recommendation(
        subject=request.subject,
        average_grade=rec_data["average_grade"],
        level=rec_data["level"],
        good_topics=rec_data["good_topics"],
        bad_topics=rec_data["bad_topics"],
        missed_topics=rec_data["missed_topics"]
    )

    return RecommendationResponse(feedback=feedback)


# =============================================================================
# EP7: Solver - Solve Single Question with RAG
# =============================================================================


async def solve_question(
    subject: str,
    grade: int,
    question: str
) -> str:
    """
    Solve a single question using RAG + LLM.

    Retrieves relevant textbook content and generates step-by-step solution.
    """
    # RAG retrieval
    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=question,
        subject=subject,
        grade=grade
    )

    # Format context from retrieved documents
    context, _ = format_context(docs, max_chars=6000, subject=subject)

    # Build prompt
    prompt = build_solver_prompt(
        subject=subject,
        grade=grade,
        question=question,
        context=context
    )

    full_prompt = f"{SOLVER_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate solution
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.3,  # Lower temperature for more precise answers
        max_tokens=1500   # Allow longer responses for detailed explanations
    )

    return response


async def solver_endpoint(request: SolverRequest) -> SolverResponse:
    """
    EP7: Solve a single question with RAG-grounded explanation.

    Uses textbook content to provide step-by-step solution.
    Note: Route is registered in router.py at /solver (not under /teacher).
    """
    answer_explained = await solve_question(
        subject=request.subject,
        grade=request.grade,
        question=request.question
    )

    return SolverResponse(
        question=request.question,
        answer_explained=answer_explained
    )


# =============================================================================
# EP3: Generate Notes
# =============================================================================


async def generate_level_notes(
    subject: str,
    grade: int,
    level: str,
    topic_definition: str,
    gap_warnings: list[str] | None = None,
    aggregated_gaps: dict | None = None
) -> dict:
    """
    Generate notes for a student level using RAG + LLM.

    Args:
        subject: Subject name
        grade: Grade level (8 or 9)
        level: Student level (weak/medium/strong)
        topic_definition: Topic description
        gap_warnings: (deprecated) Simple list of topics
        aggregated_gaps: Aggregated statistics from aggregate_student_gaps()

    Returns:
        dict with 'title', 'contents', 'teacher_notes', 'references'
    """
    # RAG retrieval
    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=topic_definition,
        subject=subject,
        grade=grade
    )

    # Format context and get references
    context, references = format_context(docs, max_chars=6000, subject=subject)

    # Build prompt with aggregated gaps
    prompt = build_level_notes_prompt(
        subject=subject,
        grade=grade,
        level=level,
        topic_definition=topic_definition,
        context=context,
        gap_warnings=gap_warnings,
        aggregated_gaps=aggregated_gaps
    )

    full_prompt = f"{NOTES_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate notes
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=2500
    )

    # Parse JSON response and add references
    result = _parse_notes_json(response, topic_definition)
    result["references"] = references
    return result


async def generate_individual_notes(
    subject: str,
    grade: int,
    topic_definition: str,
    student_info: dict | None = None,
    aggregated_gaps: dict | None = None,
    level: str | None = None
) -> dict:
    """
    Generate notes for specific students using RAG + LLM.

    Args:
        subject: Subject name
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        student_info: (deprecated) Single student data - use aggregated_gaps
        aggregated_gaps: Aggregated statistics from aggregate_student_gaps()
        level: Target level for the notes

    Returns:
        dict with 'title', 'contents', 'teacher_notes', 'references'
    """
    # RAG retrieval
    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=topic_definition,
        subject=subject,
        grade=grade
    )

    # Format context and get references
    context, references = format_context(docs, max_chars=6000, subject=subject)

    # Build prompt with aggregated gaps
    prompt = build_individual_notes_prompt(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context,
        student_info=student_info,
        aggregated_gaps=aggregated_gaps,
        level=level
    )

    full_prompt = f"{NOTES_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate notes
    llm_client = get_llm_client()
    response = await llm_client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=2500
    )

    # Parse JSON response and add references
    result = _parse_notes_json(response, topic_definition)
    result["references"] = references
    return result


@router.post("/notes/by-level", response_model=NotesResponse, response_model_exclude_none=True)
async def generate_notes_by_level(
    request: GenerateLevelNotesRequest
) -> NotesResponse:
    """
    EP3.1: Generate notes for students by level.

    Generates lesson notes adapted to specified student levels.
    Uses aggregated statistics from all students at the specified level(s).
    """
    data_loader = get_data_loader()

    # Determine grade from class
    class_info = data_loader.get_class_info(request.class_id)
    if class_info is None:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    # Get the first level (or combine if multiple)
    if request.level_list:
        level = request.level_list[0].value
    else:
        level = "medium"

    # Get students at the specified level(s)
    all_students = data_loader.get_class_students(
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    # Filter to students at specified levels
    target_levels = {lv.value for lv in request.level_list} if request.level_list else {"medium"}
    student_ids = [
        s.student_id for s in all_students
        if s.subject_level.value in target_levels
    ]

    # Aggregate gaps across all students at this level
    aggregated_gaps = data_loader.aggregate_student_gaps(
        student_ids=student_ids,
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    # Generate notes with aggregated statistics
    result = await generate_level_notes(
        subject=request.subject,
        grade=grade,
        level=level,
        topic_definition=request.topic_definition,
        aggregated_gaps=aggregated_gaps
    )

    # Format sources and statistics for response
    sources = _format_sources(result.get("references", []))
    statistics = _build_notes_statistics(aggregated_gaps)

    return NotesResponse(
        title=result["title"],
        contents=result["contents"],
        teacher_notes=result["teacher_notes"],
        sources=sources,
        statistics=statistics
    )


@router.post("/notes/individual", response_model=NotesResponse, response_model_exclude_none=True)
async def generate_notes_individual(
    request: GenerateIndividualNotesRequest
) -> NotesResponse:
    """
    EP3.2: Generate notes for specific students.

    Generates lesson notes for selected students, using aggregated statistics
    from all students in the list (not just the first one).
    """
    data_loader = get_data_loader()

    # Determine grade from class
    class_info = data_loader.get_class_info(request.class_id)
    if class_info is None:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    if not request.student_list:
        raise HTTPException(status_code=400, detail="student_list cannot be empty")

    # Validate that at least one student exists
    all_students = data_loader.get_class_students(
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )
    student_id_set = {s.student_id for s in all_students}
    valid_students = [sid for sid in request.student_list if sid in student_id_set]

    if not valid_students:
        raise HTTPException(status_code=404, detail="No valid students found in class")

    # Determine the predominant level for the group
    student_levels = [
        s.subject_level.value for s in all_students
        if s.student_id in valid_students
    ]
    if student_levels:
        # Use the most common level
        from collections import Counter
        level = Counter(student_levels).most_common(1)[0][0]
    else:
        level = "medium"

    # Aggregate gaps across ALL students in the list
    aggregated_gaps = data_loader.aggregate_student_gaps(
        student_ids=valid_students,
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    # Generate notes with aggregated statistics
    result = await generate_individual_notes(
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
        aggregated_gaps=aggregated_gaps,
        level=level
    )

    # Format sources and statistics for response
    sources = _format_sources(result.get("references", []))
    statistics = _build_notes_statistics(aggregated_gaps)

    return NotesResponse(
        title=result["title"],
        contents=result["contents"],
        teacher_notes=result["teacher_notes"],
        sources=sources,
        statistics=statistics
    )


# =============================================================================
# EP4: Generate Test
# =============================================================================


@router.post("/test/generate", response_model=TestResponse)
async def generate_test_endpoint(
    request: GenerateTestRequest
) -> TestResponse:
    """
    EP4: Generate a pool of test questions using agentic workflow.

    Uses generate-then-validate approach:
    1. Each question is generated individually
    2. Each question is validated by a checker LLM
    3. Invalid questions are retried or downgraded in difficulty

    Generates diverse questions (multiple choice and open) at various difficulty levels.
    """
    data_loader = get_data_loader()

    # Determine grade from class
    class_info = data_loader.get_class_info(request.class_id)
    if class_info is None:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    # Lazy import to avoid grpcio/langsmith loading at startup (macOS mutex.cc issue)
    from app.graph.flows.test_gen import generate_test_pool

    # Generate validated test pool using LangGraph workflow
    validated_questions, stats = await generate_test_pool(
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
        num_questions=30,
        max_retries=2,
    )

    logger.info(f"Test generation stats: {stats}")

    # Convert raw questions to Question objects
    questions = []
    for q in validated_questions:
        try:
            # Map type string to QuestionType enum
            q_type_str = q.get("type", "open").lower()
            if q_type_str == "multiple_choice":
                q_type = QuestionType.SINGLE_CHOICE  # Standard MC = single choice
            elif q_type_str == "single_choice":
                q_type = QuestionType.SINGLE_CHOICE
            else:
                q_type = QuestionType.OPEN

            # Map difficulty string to Difficulty enum
            diff_str = q.get("difficulty", "medium").lower()
            # Map "hard" to "difficult" for enum compatibility
            if diff_str == "hard":
                diff_str = "difficult"
            difficulty = Difficulty(diff_str) if diff_str in ["easy", "medium", "difficult"] else Difficulty.MEDIUM

            # Build answer options for multiple choice
            answer_options = None
            if q_type != QuestionType.OPEN and q.get("options"):
                correct_answer = q.get("correct_answer", "").upper()
                answer_options = []
                for i, opt in enumerate(q.get("options", [])):
                    letter = chr(65 + i)  # A, B, C, D
                    is_correct = (letter == correct_answer)
                    answer_options.append(AnswerOption(answer=opt, correct=is_correct))

            question = Question(
                question=q.get("question", ""),
                type=q_type,
                difficulty=difficulty,
                answer_options=answer_options,
                explanation=q.get("explanation", ""),
                topic=q.get("topic", ""),
                subtopics=[]
            )
            questions.append(question)
        except Exception as e:
            # Log and skip malformed questions
            logger.warning(f"Failed to parse question: {e}", exc_info=True)
            logger.debug(f"Question data: {q}")
            continue

    return TestResponse(
        title=f"Тест: {request.topic_definition[:50]}",
        questions=questions
    )
