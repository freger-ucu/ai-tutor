"""
Teacher API Endpoints (T7)

Handles teacher-facing lesson preparation flow:
- Analyze class (insights, clusters)
- Generate lesson content
- Generate test pool
- Create personalized tests
- Generate post-test report
- Full pipeline (all-in-one)

All endpoints return MOCK data - will be connected to real services later.
"""

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# =============================================================================
# Request Models
# =============================================================================


class ClassAnalysisRequest(BaseModel):
    """Request to analyze a class."""
    class_id: int
    subject: str
    topic: str


class GenerateLessonRequest(BaseModel):
    """Request to generate lesson content."""
    class_id: int
    subject: str
    topic_id: str
    grade: int
    class_insights: Optional[dict] = None


class GenerateTestPoolRequest(BaseModel):
    """Request to generate exercise pool."""
    topic_id: str
    subject: str
    grade: int
    pool_size: int = 20


class ClusterAssignmentInput(BaseModel):
    """A single student's cluster assignment."""
    student_id: int
    cluster_type: str  # "weak", "medium", "strong"


class CreatePersonalizedTestsRequest(BaseModel):
    """Request to create personalized tests."""
    pool_id: str
    cluster_assignments: list[ClusterAssignmentInput]


class StudentResultInput(BaseModel):
    """A single student's result for report."""
    student_id: int
    score: float
    percentage: float


class GenerateReportRequest(BaseModel):
    """Request to generate post-test report."""
    class_id: int
    test_id: str
    student_results: list[StudentResultInput]


class FullPipelineRequest(BaseModel):
    """Request for full pipeline (all steps)."""
    class_id: int
    subject: str
    topic: str
    grade: int


# =============================================================================
# Response Models
# =============================================================================


class TopicRoutingResult(BaseModel):
    """Result of topic routing."""
    topic_id: str
    topic_name: str
    prerequisites: list[str]
    subtopics: list[str]
    page_ranges: list[str]


class ClusterDistributionInfo(BaseModel):
    """Cluster distribution info."""
    weak: int
    medium: int
    strong: int


class ClassInsights(BaseModel):
    """Insights about a class."""
    cluster_distribution: ClusterDistributionInfo
    missed_prerequisites: dict[str, list[int]]  # topic -> student_ids
    weak_topics: list[str]
    students_needing_attention: list[int]


class ClusterAssignmentOutput(BaseModel):
    """A student's cluster assignment."""
    student_id: int
    cluster_type: str
    percentile: float
    avg_score: float


class ClassAnalysisResponse(BaseModel):
    """Response for class analysis."""
    topic_routing: TopicRoutingResult
    class_insights: ClassInsights
    cluster_assignments: list[ClusterAssignmentOutput]


class SourceReference(BaseModel):
    """Reference to textbook source."""
    page_id: str
    page_title: str
    page_range: str
    relevance_score: float


class TeacherLessonResponse(BaseModel):
    """Response for generated lesson."""
    insights_summary: dict
    lesson_content: dict
    control_questions: list[str]
    sources: list[SourceReference]


class ExerciseInPool(BaseModel):
    """An exercise in the pool (with answer for teacher)."""
    id: str
    question: str
    type: str
    difficulty: str
    options: Optional[list[str]] = None
    correct_answer: str
    subtopic: str
    prerequisites: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    """Validation report for exercise pool."""
    valid_count: int
    invalid_count: int
    issues: list[str]


class ExercisePoolResponse(BaseModel):
    """Response for generated exercise pool."""
    pool_id: str
    pool: list[ExerciseInPool]
    validation_report: ValidationReport


class PersonalizedTestsResponse(BaseModel):
    """Response for personalized tests."""
    tests_by_cluster: dict[str, list[ExerciseInPool]]  # "weak" -> exercises
    student_test_assignments: dict[str, str]  # student_id -> cluster


class ClassStats(BaseModel):
    """Class statistics for report."""
    average_score: float
    median_score: float
    min_score: float
    max_score: float
    below_50_percent: int
    between_50_75_percent: int
    above_75_percent: int


class ProblemTopic(BaseModel):
    """A problematic topic in the report."""
    topic: str
    error_percentage: float
    typical_mistakes: list[str]


class AttentionStudent(BaseModel):
    """A student needing attention."""
    student_id: int
    score: float
    main_problems: list[str]
    recommendation: str


class TeacherReportResponse(BaseModel):
    """Response for post-test report."""
    class_stats: ClassStats
    problem_topics: list[ProblemTopic]
    students_needing_attention: list[AttentionStudent]
    recommendations: str


class FullPipelineResponse(BaseModel):
    """Response for full pipeline."""
    class_analysis: ClassAnalysisResponse
    teacher_lesson: TeacherLessonResponse
    test_pool: ExercisePoolResponse
    personalized_tests: PersonalizedTestsResponse


# =============================================================================
# Mock Data Generators
# =============================================================================


def _generate_mock_class_analysis(req: ClassAnalysisRequest) -> ClassAnalysisResponse:
    """Generate mock class analysis."""
    return ClassAnalysisResponse(
        topic_routing=TopicRoutingResult(
            topic_id="topic_quadratic_eq",
            topic_name="Квадратні рівняння",
            prerequisites=["Лінійні рівняння", "Розкладання на множники"],
            subtopics=["Дискримінант", "Формула коренів", "Теорема Вієта"],
            page_ranges=["45-52", "53-58"]
        ),
        class_insights=ClassInsights(
            cluster_distribution=ClusterDistributionInfo(weak=5, medium=15, strong=5),
            missed_prerequisites={"Розкладання на множники": [101, 102, 105]},
            weak_topics=["Системи лінійних рівнянь"],
            students_needing_attention=[101, 102, 107]
        ),
        cluster_assignments=[
            ClusterAssignmentOutput(student_id=101, cluster_type="weak", percentile=15.0, avg_score=4.5),
            ClusterAssignmentOutput(student_id=102, cluster_type="weak", percentile=20.0, avg_score=5.0),
            ClusterAssignmentOutput(student_id=103, cluster_type="medium", percentile=45.0, avg_score=7.0),
            ClusterAssignmentOutput(student_id=104, cluster_type="medium", percentile=55.0, avg_score=7.5),
            ClusterAssignmentOutput(student_id=105, cluster_type="strong", percentile=85.0, avg_score=10.5),
        ]
    )


def _generate_mock_lesson(req: GenerateLessonRequest) -> TeacherLessonResponse:
    """Generate mock lesson content."""
    return TeacherLessonResponse(
        insights_summary={
            "cluster_stats": "20% слабких, 60% середніх, 20% сильних",
            "critical_absences": "3 учні пропустили тему 'Розкладання на множники'",
            "recommendations": "Почніть з повторення основ"
        },
        lesson_content={
            "intro": "Квадратні рівняння - один з найважливіших типів рівнянь в алгебрі.",
            "main_material": "Квадратне рівняння має вигляд ax² + bx + c = 0, де a ≠ 0...",
            "examples": {
                "basic": "x² - 5x + 6 = 0 → D = 25 - 24 = 1 → x₁ = 2, x₂ = 3",
                "medium": "2x² - 7x + 3 = 0 → ...",
                "advanced": "x² - 2mx + m² - 1 = 0 при різних m"
            },
            "common_mistakes": [
                "Забувають про від'ємний дискримінант",
                "Плутають знаки у формулі коренів"
            ]
        },
        control_questions=[
            "Що таке дискримінант і як він впливає на кількість коренів?",
            "Як знайти суму та добуток коренів без розв'язування рівняння?",
            "Коли квадратне рівняння має один корінь?",
            "Як перевірити правильність знайдених коренів?"
        ],
        sources=[
            SourceReference(
                page_id="p_45",
                page_title="Квадратні рівняння: означення",
                page_range="45-48",
                relevance_score=0.95
            ),
            SourceReference(
                page_id="p_49",
                page_title="Дискримінант та його властивості",
                page_range="49-52",
                relevance_score=0.92
            )
        ]
    )


def _generate_mock_test_pool(req: GenerateTestPoolRequest) -> ExercisePoolResponse:
    """Generate mock exercise pool."""
    exercises = [
        ExerciseInPool(
            id=f"ex_{i:03d}",
            question=q,
            type=t,
            difficulty=d,
            options=opts,
            correct_answer=ans,
            subtopic=sub,
            prerequisites=[]
        )
        for i, (q, t, d, opts, ans, sub) in enumerate([
            ("Розв'яжіть: x² - 5x + 6 = 0", "single_choice", "easy",
             ["x=2,3", "x=-2,-3", "x=1,6", "x=0,5"], "x=2,3", "Формула коренів"),
            ("Знайдіть D: x² + 4x + 4 = 0", "open", "easy", None, "0", "Дискримінант"),
            ("Скільки коренів при D < 0?", "single_choice", "easy",
             ["0", "1", "2", "∞"], "0", "Дискримінант"),
            ("Розв'яжіть: x² - 9 = 0", "open", "easy", None, "x=±3", "Неповні рівняння"),
            ("Знайдіть D: 2x² - 3x + 1 = 0", "open", "easy", None, "1", "Дискримінант"),
            ("Розв'яжіть: x² + 2x - 15 = 0", "open", "medium", None, "x=-5,3", "Формула коренів"),
            ("Сума коренів x² - 7x + 10 = 0", "open", "medium", None, "7", "Теорема Вієта"),
            ("Добуток коренів x² - 7x + 10 = 0", "open", "medium", None, "10", "Теорема Вієта"),
            ("При якому k рівні корені: x² + kx + 9 = 0", "open", "medium", None, "k=±6", "Параметри"),
            ("Розв'яжіть: 3x² - 12x = 0", "open", "medium", None, "x=0,4", "Неповні рівняння"),
            ("Складіть рівняння з коренями 2 і 5", "open", "medium", None, "x²-7x+10=0", "Теорема Вієта"),
            ("При якому m є 2 корені: x² - 4x + m = 0", "open", "difficult", None, "m<4", "Параметри"),
            ("x + y = 7, xy = 12. Знайти x, y", "open", "difficult", None, "3,4 або 4,3", "Системи"),
            ("Більший корінь x² - 5x + 4 = 0", "open", "difficult", None, "4", "Формула коренів"),
            ("При якому k корені протилежні: x² + kx - 6 = 0", "open", "difficult", None, "k=0", "Параметри"),
            ("Розв'яжіть: |x² - 4| = 3x", "open", "difficult", None, "...", "Модуль"),
        ], start=1)
    ]

    return ExercisePoolResponse(
        pool_id="pool_001",
        pool=exercises,
        validation_report=ValidationReport(
            valid_count=len(exercises),
            invalid_count=0,
            issues=[]
        )
    )


def _generate_mock_personalized_tests(
    req: CreatePersonalizedTestsRequest
) -> PersonalizedTestsResponse:
    """Generate mock personalized tests."""
    # Create simple exercises for each cluster
    weak_exercises = [
        ExerciseInPool(id="w1", question="x² - 4 = 0", type="open", difficulty="easy",
                      correct_answer="x=±2", subtopic="Неповні"),
        ExerciseInPool(id="w2", question="x² - 5x = 0", type="open", difficulty="easy",
                      correct_answer="x=0,5", subtopic="Неповні"),
        ExerciseInPool(id="w3", question="D для x² + 2x + 1", type="open", difficulty="easy",
                      correct_answer="0", subtopic="Дискримінант"),
        ExerciseInPool(id="w4", question="x² - 1 = 0", type="open", difficulty="easy",
                      correct_answer="x=±1", subtopic="Неповні"),
        ExerciseInPool(id="w5", question="x² - 6x + 9 = 0", type="open", difficulty="medium",
                      correct_answer="x=3", subtopic="Формула"),
        ExerciseInPool(id="w6", question="Скільки коренів при D=0?", type="single_choice",
                      difficulty="easy", options=["0", "1", "2"], correct_answer="1", subtopic="Дискримінант"),
    ]

    medium_exercises = [
        ExerciseInPool(id="m1", question="x² - 5x + 6 = 0", type="open", difficulty="medium",
                      correct_answer="x=2,3", subtopic="Формула"),
        ExerciseInPool(id="m2", question="2x² - 7x + 3 = 0", type="open", difficulty="medium",
                      correct_answer="x=0.5,3", subtopic="Формула"),
        ExerciseInPool(id="m3", question="Сума коренів x² - 9x + 20", type="open", difficulty="medium",
                      correct_answer="9", subtopic="Вієта"),
        ExerciseInPool(id="m4", question="x² + 4x - 5 = 0", type="open", difficulty="medium",
                      correct_answer="x=-5,1", subtopic="Формула"),
        ExerciseInPool(id="m5", question="При якому k D=0: x² + kx + 4 = 0", type="open",
                      difficulty="medium", correct_answer="k=±4", subtopic="Параметри"),
        ExerciseInPool(id="m6", question="Складіть рівняння: x₁=1, x₂=4", type="open",
                      difficulty="medium", correct_answer="x²-5x+4=0", subtopic="Вієта"),
        ExerciseInPool(id="m7", question="3x² - 12x = 0", type="open", difficulty="easy",
                      correct_answer="x=0,4", subtopic="Неповні"),
        ExerciseInPool(id="m8", question="x² - 8x + 15 = 0", type="open", difficulty="medium",
                      correct_answer="x=3,5", subtopic="Формула"),
    ]

    strong_exercises = [
        ExerciseInPool(id="s1", question="При якому m 2 корені: x² - 6x + m = 0", type="open",
                      difficulty="difficult", correct_answer="m<9", subtopic="Параметри"),
        ExerciseInPool(id="s2", question="x + y = 10, xy = 21", type="open", difficulty="difficult",
                      correct_answer="x=3,y=7", subtopic="Системи"),
        ExerciseInPool(id="s3", question="Більший корінь x² - 7x + 10 = 0", type="open",
                      difficulty="medium", correct_answer="5", subtopic="Формула"),
        ExerciseInPool(id="s4", question="При якому k корені x² + kx + k = 0 взаємно обернені",
                      type="open", difficulty="difficult", correct_answer="k=1", subtopic="Параметри"),
        ExerciseInPool(id="s5", question="x⁴ - 5x² + 4 = 0", type="open", difficulty="difficult",
                      correct_answer="x=±1,±2", subtopic="Біквадратні"),
        ExerciseInPool(id="s6", question="2x² - 7x + 3 = 0", type="open", difficulty="medium",
                      correct_answer="x=0.5,3", subtopic="Формула"),
        ExerciseInPool(id="s7", question="x² - (m+1)x + m = 0, знайти m якщо x₁ = 2x₂",
                      type="open", difficulty="difficult", correct_answer="m=2", subtopic="Параметри"),
        ExerciseInPool(id="s8", question="Сума квадратів коренів x² - 5x + 3 = 0",
                      type="open", difficulty="difficult", correct_answer="19", subtopic="Вієта"),
        ExerciseInPool(id="s9", question="x² + |x| - 6 = 0", type="open", difficulty="difficult",
                      correct_answer="x=±2", subtopic="Модуль"),
        ExerciseInPool(id="s10", question="При якому a рівняння x² + ax + a² = 0 має корені",
                      type="open", difficulty="difficult", correct_answer="a=0", subtopic="Параметри"),
    ]

    # Build student assignments
    assignments = {str(a.student_id): a.cluster_type for a in req.cluster_assignments}

    return PersonalizedTestsResponse(
        tests_by_cluster={
            "weak": weak_exercises,
            "medium": medium_exercises,
            "strong": strong_exercises
        },
        student_test_assignments=assignments
    )


def _generate_mock_report(req: GenerateReportRequest) -> TeacherReportResponse:
    """Generate mock post-test report."""
    return TeacherReportResponse(
        class_stats=ClassStats(
            average_score=72.5,
            median_score=75.0,
            min_score=35.0,
            max_score=98.0,
            below_50_percent=4,
            between_50_75_percent=12,
            above_75_percent=9
        ),
        problem_topics=[
            ProblemTopic(
                topic="Параметричні рівняння",
                error_percentage=65.0,
                typical_mistakes=[
                    "Не враховують умову D ≥ 0",
                    "Плутають знаки нерівності"
                ]
            ),
            ProblemTopic(
                topic="Теорема Вієта",
                error_percentage=40.0,
                typical_mistakes=[
                    "Плутають суму і добуток",
                    "Забувають про знак c/a"
                ]
            )
        ],
        students_needing_attention=[
            AttentionStudent(
                student_id=101,
                score=35.0,
                main_problems=["Не розуміє поняття дискримінанта", "Пропустив базові теми"],
                recommendation="Індивідуальні консультації, повторення основ"
            ),
            AttentionStudent(
                student_id=107,
                score=42.0,
                main_problems=["Обчислювальні помилки", "Неуважність"],
                recommendation="Більше практики з простими прикладами"
            )
        ],
        recommendations="Рекомендую на наступному уроці повторити тему 'Параметричні рівняння'. "
                       "Зверніть особливу увагу на учнів 101 та 107 - їм потрібна додаткова підтримка. "
                       "Для сильних учнів можна запропонувати олімпіадні задачі."
    )


def _generate_mock_full_pipeline(req: FullPipelineRequest) -> FullPipelineResponse:
    """Generate mock full pipeline response."""
    analysis_req = ClassAnalysisRequest(
        class_id=req.class_id,
        subject=req.subject,
        topic=req.topic
    )
    lesson_req = GenerateLessonRequest(
        class_id=req.class_id,
        subject=req.subject,
        topic_id="topic_001",
        grade=req.grade
    )
    pool_req = GenerateTestPoolRequest(
        topic_id="topic_001",
        subject=req.subject,
        grade=req.grade
    )
    personalize_req = CreatePersonalizedTestsRequest(
        pool_id="pool_001",
        cluster_assignments=[
            ClusterAssignmentInput(student_id=101, cluster_type="weak"),
            ClusterAssignmentInput(student_id=102, cluster_type="medium"),
            ClusterAssignmentInput(student_id=103, cluster_type="strong"),
        ]
    )

    return FullPipelineResponse(
        class_analysis=_generate_mock_class_analysis(analysis_req),
        teacher_lesson=_generate_mock_lesson(lesson_req),
        test_pool=_generate_mock_test_pool(pool_req),
        personalized_tests=_generate_mock_personalized_tests(personalize_req)
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/analyze-class", response_model=ClassAnalysisResponse)
async def analyze_class(request: ClassAnalysisRequest) -> ClassAnalysisResponse:
    """
    Analyze a class for a specific topic.

    Returns:
    - Topic routing (matched topic, prerequisites)
    - Class insights (clusters, absences, weak areas)
    - Cluster assignments for each student
    """
    return _generate_mock_class_analysis(request)


@router.post("/generate-lesson", response_model=TeacherLessonResponse)
async def generate_lesson(request: GenerateLessonRequest) -> TeacherLessonResponse:
    """
    Generate lesson content (Конспект #1) for teacher.

    Returns structured lesson with:
    - Insights summary
    - Main content with examples by level
    - Control questions
    - Textbook references
    """
    return _generate_mock_lesson(request)


@router.post("/generate-test-pool", response_model=ExercisePoolResponse)
async def generate_test_pool(request: GenerateTestPoolRequest) -> ExercisePoolResponse:
    """
    Generate exercise pool for a topic.

    Returns 15-20 exercises with:
    - Mixed difficulties (easy/medium/hard)
    - Mixed types (choice/open)
    - Correct answers (for teacher review)
    - Validation report
    """
    return _generate_mock_test_pool(request)


@router.post("/create-personalized-tests", response_model=PersonalizedTestsResponse)
async def create_personalized_tests(
    request: CreatePersonalizedTestsRequest
) -> PersonalizedTestsResponse:
    """
    Create personalized tests for each cluster.

    Distributes exercises based on:
    - Weak: more easy, fewer hard
    - Medium: balanced mix
    - Strong: more hard, fewer easy
    """
    return _generate_mock_personalized_tests(request)


@router.post("/generate-report", response_model=TeacherReportResponse)
async def generate_report(request: GenerateReportRequest) -> TeacherReportResponse:
    """
    Generate post-test report for teacher.

    Includes:
    - Class statistics
    - Problem topics
    - Students needing attention
    - Recommendations
    """
    return _generate_mock_report(request)


@router.post("/full-pipeline", response_model=FullPipelineResponse)
async def full_pipeline(request: FullPipelineRequest) -> FullPipelineResponse:
    """
    Run full teacher pipeline in one call.

    Combines:
    1. Class analysis
    2. Lesson generation
    3. Test pool generation
    4. Test personalization
    """
    return _generate_mock_full_pipeline(request)
