# AI Tutor Backend - Implementation Status

## Overview

The AI Tutor backend is a FastAPI application that provides APIs for an educational tutoring system. It supports both teacher and student workflows for Ukrainian school curriculum.

**Current Status:** Phase 1 complete, Phase 2 partially complete

| Task | Description | Status |
|------|-------------|--------|
| T0 | Monorepo Structure | Done |
| T1 | DataLoader Service | Done |
| T2 | Pydantic Models | Done |
| T3 | Config + Health + Docker | Done |
| T4 | Topic Routing Service | Pending |
| T5 | Clustering Service | Done |
| T6 | Student API Stubs | Done |
| T7 | Teacher API Stubs | Done |

**Test Coverage:** 238 tests passing

---

## T0: Monorepo Structure

Basic project structure with FastAPI application.

### Files
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings management
│   ├── api/
│   │   └── v1/
│   │       ├── health.py    # Health endpoints
│   │       ├── student.py   # Student API
│   │       └── teacher.py   # Teacher API
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   └── utils/
├── tests/
├── data/                    # Parquet data files
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

### Running the App
```bash
cd backend
uvicorn app.main:app --reload
```

---

## T1: DataLoader Service

Loads and queries student/teacher data from Parquet files.

### Location
`app/services/data_loader.py`

### Key Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `get_teacher_classes(teacher_id)` | Get all classes a teacher teaches | `list[ClassInfo]` |
| `get_class_students(class_id, subject)` | Get all students in a class for a subject | `list[StudentSummary]` |
| `get_student_details(student_id, class_id, subject)` | Get detailed student info including absences and problem topics | `StudentDetails` |
| `get_student_info(student_id)` | Get basic student info across all subjects | `StudentInfo` |
| `get_students_by_level(class_id, subject, levels)` | Filter students by performance level | `list[StudentSummary]` |

### Data Sources
- `data/benchmark_scores.parquet` - Student grades by topic
- `data/benchmark_absences.parquet` - Student absences
- `data/toc/` - Table of contents (curriculum structure)

### Usage
```python
from app.services.data_loader import get_data_loader

loader = get_data_loader()
classes = loader.get_teacher_classes(teacher_id=1)
students = loader.get_class_students(class_id=101, subject="Алгебра")
```

---

## T2: Pydantic Models

Type-safe data models for API requests/responses.

### Location
- `app/models/domain.py` - Core business objects
- `app/models/enums.py` - Enumerations
- `app/models/requests.py` - API request models
- `app/models/responses.py` - API response models
- `app/models/state.py` - State management models

### Key Models

**Enums:**
- `Level` - Student performance level: `weak`, `medium`, `strong`
- `Difficulty` - Question difficulty: `easy`, `medium`, `difficult`
- `QuestionType` - Question type: `single_choice`, `multiple_choice`, `open`

**Domain Models:**
```python
class ClassInfo(BaseModel):
    class_id: int
    class_number: int      # Grade: 8, 9, etc.
    subject: str           # "Алгебра", "Геометрія", etc.

class StudentSummary(BaseModel):
    student_id: int
    subject_level: Level
    average_subject_grade: float  # 0-12 scale

class Question(BaseModel):
    question: str
    type: QuestionType
    difficulty: Difficulty
    answer_options: Optional[list[AnswerOption]]
    explanation: str
    topic: str
    subtopics: list[str]
```

---

## T3: Config + Health + Docker

Application configuration and infrastructure.

### Configuration

**Location:** `app/config.py`

**Key Settings:**
```python
class Settings(BaseSettings):
    # App
    app_name: str = "AI Tutor"
    app_version: str = "0.1.0"
    debug: bool = False

    # Data paths
    data_dir: Path = Path("data")
    scores_path: Path      # Auto-computed
    absences_path: Path    # Auto-computed

    # LLM
    llm_model_name: str = ""
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
```

**Environment Variables:** See `.env.example`

### Health Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | Basic health check | `{"status": "healthy", "version": "0.1.0"}` |
| `GET /health/live` | Kubernetes liveness probe | `{"status": "alive"}` |
| `GET /health/ready` | Kubernetes readiness probe | `{"status": "ready", "checks": {...}}` |

### Docker

```bash
# Build and run
docker-compose up --build

# Services
# - backend: FastAPI app on port 8000
# - redis: Cache on port 6379
```

---

## T5: Clustering Service

Groups students into weak/medium/strong clusters based on grades.

### Location
`app/services/clustering.py`

### Algorithm
Uses quartile-based clustering:
1. Calculate Q1 (25th percentile) and Q3 (75th percentile) using linear interpolation
2. Assign clusters:
   - **weak:** score < Q1
   - **medium:** Q1 ≤ score ≤ Q3
   - **strong:** score > Q3

### Key Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `cluster_students(class_id, subject)` | Get all 3 clusters for a class | `list[StudentCluster]` |
| `get_cluster_for_student(student_id, class_id, subject)` | Get cluster assignment for one student | `ClusterAssignment` |
| `get_cluster_distribution(class_id, subject)` | Get distribution stats | `ClusterDistribution` |

### Models

```python
class StudentCluster(BaseModel):
    cluster_type: Level              # weak/medium/strong
    student_ids: list[int]
    avg_score: float
    score_range: tuple[float, float] # (min, max)

class ClusterAssignment(BaseModel):
    student_id: int
    cluster_type: Level
    avg_score: float
    percentile: float                # 0-100

class ClusterDistribution(BaseModel):
    weak_count: int
    medium_count: int
    strong_count: int
    weak_percentage: float
    medium_percentage: float
    strong_percentage: float
    total_count: int
```

### Usage
```python
from app.services.clustering import get_clustering_service

service = get_clustering_service()
clusters = service.cluster_students(class_id=101, subject="Алгебра")
distribution = service.get_cluster_distribution(class_id=101, subject="Алгебра")
```

---

## T6: Student API Stubs

Mock endpoints for student test-taking flow.

### Location
`app/api/v1/student.py`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/student/{student_id}/test?test_id=X` | Get test exercises (no answers) |
| POST | `/api/v1/student/submit` | Submit test answers |
| GET | `/api/v1/student/{student_id}/result/{test_id}` | Get test results |
| GET | `/api/v1/student/{student_id}/summary/{test_id}` | Get personalized summary |

### Response Models

**GET /test** - Returns exercises without correct answers:
```python
class StudentTestResponse(BaseModel):
    test_id: str
    exercises: list[ExerciseForStudent]  # No correct_answer field
    time_limit_minutes: Optional[int]
```

**POST /submit** - Submit answers:
```python
class SubmitAnswersRequest(BaseModel):
    student_id: int
    test_id: str
    answers: list[StudentAnswer]

class SubmitAnswersResponse(BaseModel):
    submission_id: str
    status: str  # "received"
```

**GET /result** - Test results:
```python
class StudentResultResponse(BaseModel):
    score: float
    percentage: float
    correct_count: int
    total_count: int
    correct_subtopics: list[str]
    failed_subtopics: list[str]
    error_patterns: list[ErrorPattern]
    class_percentile: float
```

**GET /summary** - Personalized learning summary:
```python
class StudentSummaryResponse(BaseModel):
    result_section: dict
    prerequisites_review: Optional[dict]
    mistakes_analysis: list[dict]
    practice_exercises: list[dict]
    recommendations: str
```

### Note
All endpoints currently return **mock data** with realistic Ukrainian math content (quadratic equations theme). Will be connected to real services later.

---

## T7: Teacher API Stubs

Mock endpoints for teacher lesson preparation flow.

### Location
`app/api/v1/teacher.py`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/teacher/analyze-class` | Analyze class performance |
| POST | `/api/v1/teacher/generate-lesson` | Generate lesson content |
| POST | `/api/v1/teacher/generate-test-pool` | Generate exercise pool |
| POST | `/api/v1/teacher/create-personalized-tests` | Create tests per cluster |
| POST | `/api/v1/teacher/generate-report` | Generate class report |
| POST | `/api/v1/teacher/full-pipeline` | Run complete workflow |

### Request/Response Models

**POST /analyze-class:**
```python
class ClassAnalysisRequest(BaseModel):
    teacher_id: int
    class_id: int
    subject: str
    topic: str

class ClassAnalysisResponse(BaseModel):
    topic_routing_result: TopicRoutingResult
    class_insights: ClassInsights
    cluster_assignments: list[ClusterAssignmentInfo]
```

**POST /generate-lesson:**
```python
class GenerateLessonRequest(BaseModel):
    teacher_id: int
    class_id: int
    subject: str
    topic: str
    class_insights: Optional[dict] = None

class TeacherLessonResponse(BaseModel):
    insights_summary: str
    prerequisites_review: str
    lesson_content: str
    control_questions: list[str]
    sources: list[str]
```

**POST /generate-test-pool:**
```python
class GenerateTestPoolRequest(BaseModel):
    teacher_id: int
    class_id: int
    subject: str
    topic: str
    pool_size: int = 15

class ExercisePoolResponse(BaseModel):
    exercises: list[ExerciseWithAnswer]
    validation_report: ValidationReport
```

**POST /create-personalized-tests:**
```python
class CreatePersonalizedTestsRequest(BaseModel):
    teacher_id: int
    class_id: int
    subject: str
    topic: str
    exercise_pool: Optional[list[dict]] = None

class PersonalizedTestsResponse(BaseModel):
    weak_test: ClusterTest
    medium_test: ClusterTest
    strong_test: ClusterTest
```

**POST /full-pipeline:**
```python
class FullPipelineRequest(BaseModel):
    teacher_id: int
    class_id: int
    subject: str
    topic: str

class FullPipelineResponse(BaseModel):
    class_analysis: ClassAnalysisResponse
    lesson: TeacherLessonResponse
    exercise_pool: ExercisePoolResponse
    personalized_tests: PersonalizedTestsResponse
    report: TeacherReportResponse
```

### Note
All endpoints currently return **mock data**. Will be connected to LLM services (T4+) later.

---

## Running Tests

```bash
cd backend

# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_services/test_clustering.py -v

# Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=html
```

### Test Structure
```
tests/
├── conftest.py                    # Shared fixtures
├── test_api/
│   ├── test_student.py            # T6 tests (29 tests)
│   └── test_teacher.py            # T7 tests (31 tests)
├── test_models/
│   ├── test_domain.py
│   ├── test_requests.py
│   └── test_responses.py
└── test_services/
    ├── test_clustering.py         # T5 tests (18 tests)
    └── test_data_loader.py        # T1 tests
```

---

## Next Steps

### T4: Topic Routing Service (Pending)
AI-based service that:
1. Analyzes a topic to find prerequisites
2. Identifies what subtopics students struggle with
3. Routes to appropriate remediation content

Will integrate with LLMs (Claude/GPT) for intelligent topic analysis.

### Future Tasks
- T8+: Connect stubs to real LLM services
- T9+: Implement RAG for curriculum content
- T10+: Student progress tracking
- T11+: Analytics dashboard
