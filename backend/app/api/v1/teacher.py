"""
Teacher API Endpoints

Implements EP1-EP6 per architecture.md contracts.
"""

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

from app.models.requests import (
    GetStudentListRequest,
    StudentDetailsRequest,
    StudentRecommendationRequest,
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
    NotesResponse,
    NotesStatistics,
    TopicStatistic,
    TestResponse,
)
from app.models.domain import Question, AnswerOption
from app.models.enums import QuestionType, Difficulty
from app.services.data_loader import get_data_loader
from app.rag.utils.llm_client import get_llm_client
from app.prompts.recommendation import (
    RECOMMENDATION_SYSTEM_PROMPT,
    build_recommendation_prompt,
)
# Notes generation now uses the LangGraph flow in app.graph.flows.notes

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
        max_tokens=1500
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
# EP3: Generate Notes
# =============================================================================


@router.post("/notes/by-level", response_model=NotesResponse, response_model_exclude_none=True)
async def generate_notes_by_level(
    request: GenerateLevelNotesRequest
) -> NotesResponse:
    """
    EP3.1: Generate notes for students by level.

    Generates lesson notes adapted to student levels.
    Uses LangGraph flow that:
    1. Analyzes students to compute level and aggregate gaps
    2. Filters gaps to prerequisites using LLM
    3. Retrieves RAG context for topic and prerequisites
    4. Generates notes with optional recap section

    If level_list is provided, filters students to those levels.
    If level_list is empty, includes all students in the class.
    The level is computed from the selected students' scores.
    """
    from app.graph.flows.notes import generate_notes

    data_loader = get_data_loader()

    # Determine grade from class
    class_info = data_loader.get_class_info(request.class_id)
    if class_info is None:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    # Get all students in class
    all_students = data_loader.get_class_students(
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    if not all_students:
        raise HTTPException(
            status_code=404,
            detail="No students found for this class/subject combination"
        )

    # Filter students by requested levels (or take all if empty)
    if request.level_list:
        target_levels = {lv.value for lv in request.level_list}
        student_ids = [
            s.student_id for s in all_students
            if s.subject_level.value in target_levels
        ]
        if not student_ids:
            raise HTTPException(
                status_code=404,
                detail="No students found at specified levels"
            )
    else:
        # No levels specified → all students
        student_ids = [s.student_id for s in all_students]

    # Generate notes - level will be computed from student scores
    result = await generate_notes(
        student_ids=student_ids,
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Format sources for response
    sources = _format_sources(result.get("references", []))

    # Build statistics from the flow's aggregated_gaps (need to get from data_loader for response)
    aggregated_gaps = data_loader.aggregate_student_gaps(
        student_ids=student_ids,
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )
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

    Generates lesson notes for selected students.
    Uses LangGraph flow that:
    1. Analyzes students to compute level and gaps
    2. Filters gaps to prerequisites using LLM
    3. Retrieves RAG context for topic and prerequisites
    4. Generates notes with optional recap section
    """
    from app.graph.flows.notes import generate_notes

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

    # Generate notes using LangGraph flow
    result = await generate_notes(
        student_ids=valid_students,
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
    )

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    # Format sources for response
    sources = _format_sources(result.get("references", []))

    # Build statistics from the flow's aggregated_gaps (need to get from data_loader for response)
    aggregated_gaps = data_loader.aggregate_student_gaps(
        student_ids=valid_students,
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )
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

    Always generates 12 questions with difficulty determined post-factum.
    Uses level-aware generation based on selected students.

    Student selection (priority):
    1. student_list - specific students if provided
    2. level_list - students at specified levels if provided
    3. all students in class if neither provided

    The median level of selected students influences question style.
    """
    data_loader = get_data_loader()

    # Determine grade from class
    class_info = data_loader.get_class_info(request.class_id)
    if class_info is None:
        raise HTTPException(status_code=404, detail="Class not found")

    grade = class_info["class_number"]

    # Get all students in class
    all_students = data_loader.get_class_students(
        class_id=request.class_id,
        subject=request.subject,
        teacher_id=request.teacher_id
    )

    if not all_students:
        raise HTTPException(
            status_code=404,
            detail="No students found for this class/subject combination"
        )

    # Select students (priority: student_list > level_list > all)
    if request.student_list:
        student_id_set = set(request.student_list)
        selected_students = [s for s in all_students if s.student_id in student_id_set]
    elif request.level_list:
        target_levels = {lv.value for lv in request.level_list}
        selected_students = [s for s in all_students if s.subject_level.value in target_levels]
    else:
        selected_students = all_students

    if not selected_students:
        raise HTTPException(status_code=404, detail="No matching students found")

    # Compute median level for prompt adjustment
    from app.services.levels import compute_median_level
    selected_scores = [s.average_subject_grade for s in selected_students]
    all_scores = [s.average_subject_grade for s in all_students]
    median_level = compute_median_level(selected_scores, all_scores)

    logger.info(f"EP4: {len(selected_students)} students selected, median_level={median_level}")

    # Lazy import to avoid grpcio/langsmith loading at startup (macOS mutex.cc issue)
    from app.graph.flows.test_gen import generate_test_pool

    # Generate validated test pool using LangGraph workflow
    validated_questions, stats = await generate_test_pool(
        subject=request.subject,
        grade=grade,
        topic_definition=request.topic_definition,
        level=median_level,
    )

    logger.info(
        f"Test generation complete: {stats.total_questions} questions "
        f"(easy={stats.easy_count}, medium={stats.medium_count}, hard={stats.hard_count}, "
        f"single_choice={stats.single_choice_count}, multiple_choice={stats.multiple_choice_count}, open={stats.open_count}), "
        f"LLM calls={stats.total_llm_calls}"
    )

    # Convert raw questions to Question objects
    questions = []
    for q in validated_questions:
        try:
            # Map type string to QuestionType enum
            q_type_str = q.get("type", "open").lower()
            if q_type_str == "multiple_choice":
                q_type = QuestionType.MULTIPLE_CHOICE
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
                # Determine correct answers based on question type
                correct_indices_set: set[int] = set()

                if q_type == QuestionType.MULTIPLE_CHOICE:
                    # Multiple choice: uses correct_answer_indices (list of ints)
                    correct_indices = q.get("correct_answer_indices", [])
                    if isinstance(correct_indices, list):
                        correct_indices_set = {i for i in correct_indices if isinstance(i, int)}
                else:
                    # Single choice: uses correct_answer_index (int) or correct_answer (letter)
                    correct_index = q.get("correct_answer_index")
                    if correct_index is None:
                        # Fallback to old letter format
                        correct_letter = q.get("correct_answer", "").upper()
                        letter_to_index = {"A": 0, "B": 1, "C": 2, "D": 3}
                        correct_index = letter_to_index.get(correct_letter, -1)
                    if isinstance(correct_index, int) and correct_index >= 0:
                        correct_indices_set = {correct_index}

                answer_options = []
                for i, opt in enumerate(q.get("options", [])):
                    is_correct = (i in correct_indices_set)
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
