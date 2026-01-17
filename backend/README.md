# AI Tutor Backend

FastAPI backend for the AI Tutor system - an AI-powered educational platform that provides personalized learning experiences for students and teaching tools for educators.

## Features

- **Test Generation**: Create customized tests based on topics and difficulty levels
- **Lesson Notes**: Generate level-appropriate lesson materials with prerequisite awareness
- **Answer Evaluation**: Evaluate open-ended student answers with detailed feedback
- **Student Feedback**: Provide topic-grouped performance analysis
- **RAG System**: Hybrid retrieval (BM25 + vector search) grounded in official textbooks
- **Multi-subject Support**: Algebra, Ukrainian Language, Ukrainian History (Grades 8-9)

## Requirements

- Python 3.11+
- Redis (optional, for caching)

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Main LLM provider for reasoning-intensive tasks
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4.1-mini

# Task-specific providers for simpler operations (recommendations, feedback)
TASK_PROVIDER_FEEDBACK=mamay
TASK_PROVIDER_RECOMMENDATION=mamay

# Lapa/Mamay configuration (for cost-efficient simple tasks)
LAPA_API_KEY=your-lapa-api-key
LAPA_BASE_URL=http://146.59.127.106:4000
LAPA_MODEL=mamay

# Phoenix Telemetry (optional - LLM Observability)
PHOENIX_ENABLED=false
PHOENIX_ENDPOINT=

# LangSmith Tracing (optional)
LANGSMITH_ENABLED=false
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=ai-tutor
```

See `.env.example` for all available configuration options.

### 4. Prepare Data Files

The `data/` directory is not included in the repository. You need to add the following files:

```
data/
├── benchmark_scores.parquet       # Student performance data
├── benchmark_absences.parquet     # Attendance records
└── embeddings/
    ├── pages_for_hackathon.parquet              # Textbook page embeddings
    └── toc_for_hackathon_with_subtopics.parquet # Table of contents with embeddings
```

**Data file formats:**

| File | Required Columns |
|------|------------------|
| `benchmark_scores.parquet` | `student_id`, `class_id`, `subject`, `topic`, `score`, `date` |
| `benchmark_absences.parquet` | `student_id`, `class_id`, `subject`, `topic`, `date` |
| `pages_for_hackathon.parquet` | `page_id`, `content`, `embedding`, `subject`, `grade` |
| `toc_for_hackathon_with_subtopics.parquet` | `topic_id`, `topic_name`, `subtopics`, `embedding`, `subject`, `grade` |

Contact the team for access to the data files.

### 5. Run the Development Server

```bash
uvicorn app.main:app --reload
```

The server starts at **http://localhost:8000**

### 6. Run with Custom Port

```bash
uvicorn app.main:app --reload --port 8001
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Health Checks

- **Liveness**: `GET /health/live` - Basic health check
- **Readiness**: `GET /health/ready` - Full system readiness
- **Status**: `GET /health/status` - Detailed system status


## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API routes (teacher, student, health)
│   ├── graph/            # LangGraph workflows
│   │   ├── flows/        # Individual flow implementations
│   │   └── shared/       # Reusable RAG/LLM components
│   ├── models/           # Pydantic data models
│   ├── prompts/          # LLM prompt templates
│   ├── rag/              # RAG system (hybrid retrieval)
│   ├── services/         # Business logic services
│   ├── telemetry/        # Observability setup
│   ├── utils/            # Helper utilities
│   ├── config.py         # Settings management
│   └── main.py           # FastAPI app entry point
├── data/                 # Runtime data (gitignored)
├── docs/                 # Documentation
│   ├── architecture.md   # Technical architecture
│   ├── business-value.md # Business value per endpoint
│   └── api-contracts.md  # Complete API specifications
├── tests/                # Test suites
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata
└── pytest.ini            # Test configuration
```

## Configuration Reference

### LLM Providers

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | Main LLM provider (`openai`, `gemini`, `lapa`) |
| `TASK_PROVIDER_FEEDBACK` | `mamay` | Provider for feedback generation |
| `TASK_PROVIDER_RECOMMENDATION` | `mamay` | Provider for recommendations |

### OpenAI (Primary - Complex Reasoning Tasks)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI model for reasoning tasks |

### Lapa/Mamay (Simple Tasks)

| Variable | Default | Description |
|----------|---------|-------------|
| `LAPA_API_KEY` | - | Lapa API key |
| `LAPA_BASE_URL` | `http://146.59.127.106:4000` | Lapa API endpoint |
| `LAPA_MODEL` | `mamay` | Mamay model for simple tasks |

### Gemini (Alternative)

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | Gemini API key |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |

### General Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_TEMPERATURE` | `0.0` | Generation temperature |
| `LLM_MAX_TOKENS` | `500` | Max output tokens |
| `BACKEND_PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode |
| `PHOENIX_ENABLED` | `false` | Enable Phoenix telemetry |
| `LANGSMITH_ENABLED` | `false` | Enable LangSmith tracing |

## API Endpoints Overview

### Teacher Endpoints (EP1-EP6)
- `GET /api/v1/teacher/{teacher_id}` - EP1: Get teacher's classes and subjects
- `POST /api/v1/teacher/students` - EP2: Get students in a class with levels
- `POST /api/v1/teacher/notes/by-level` - EP3.1: Generate notes by student level
- `POST /api/v1/teacher/notes/individual` - EP3.2: Generate notes for specific students
- `POST /api/v1/teacher/test/generate` - EP4: Generate validated test questions
- `POST /api/v1/teacher/student/details` - EP5: Get detailed student performance
- `POST /api/v1/teacher/student/recommendation` - EP6: Get AI teaching recommendations

### Student Endpoints (EP8-EP10)
- `GET /api/v1/student/{student_id}` - EP8: Get student's class and subjects with levels
- `POST /api/v1/student/check-open` - EP9: Evaluate open-ended answer (RAG-grounded)
- `POST /api/v1/student/test-feedback` - EP10: Get feedback after completing a test

## Documentation

For detailed documentation, see:

- [Architecture](docs/architecture.md) - Technical architecture and design patterns
- [Business Value](docs/business-value.md) - Business value of each endpoint
- [API Contracts](docs/api-contracts.md) - Complete API specifications with examples

## LangGraph Studio (Local Development)

LangGraph Studio allows you to visualize and debug LangGraph flows locally.

### Setup

1. Install LangGraph CLI:
```bash
pip install langgraph-cli
```

2. Run the studio:
```bash
cd backend
langgraph dev
```

3. Open the Studio UI at the URL shown in the terminal (usually http://localhost:8123)

### Available Graphs

| Graph | Endpoint | Description |
|-------|----------|-------------|
| notes | EP3 | Generate lesson notes with prerequisite-aware recap |
| test_gen | EP4 | Generate validated test questions with planning-based parallel architecture |
| check_answer | EP9 | Evaluate open-ended answers using RAG-grounded evaluation |
| feedback | EP10 | Generate concise test feedback (for student, no greetings) |
| recommendation | EP6 | Generate concise teaching recommendations (factual, no greetings) |

### Test Gen Graph Input

The test_gen graph uses a planning-based architecture with 8 nodes:
1. **retrieve_context** - Get base topic context from RAG
2. **plan_test** - LLM plans test structure (12 question specs, no difficulty at this stage)
3. **retrieve_concepts** - Parallel RAG retrieval for each concept
4. **batch_generate** - Parallel question generation (10 concurrent)
5. **batch_validate** - CPU + LLM validation (format checks, then content validation)
6. **prepare_retry** - Queue failed specs for retry (max 1 iteration)
7. **classify_difficulty** - Batch LLM classification of all questions (post-factum)
8. **finalize** - Log stats and return validated questions

Input fields:
- `subject`: Subject name (`Алгебра`, `Українська мова`, `Історія України`)
- `grade`: Grade level (`8` or `9`)
- `topic_definition`: Topic for the test
- `level`: Student level for prompt guidance (`weak`, `medium`, `strong`) - optional, defaults to `medium`

Note: Always generates 12 questions. Difficulty is classified post-factum using subject-specific criteria.
Question types: `single_choice` (1 correct), `multiple_choice` (2-3 correct), `open`.

### Notes Graph Input

The notes graph requires only 4 input fields:
- `student_ids`: List of student IDs (e.g., `[1, 2, 3]`)
- `subject`: Subject name (`Алгебра`, `Українська мова`, `Історія України`)
- `grade`: Grade level (`8` or `9`)
- `topic_definition`: Topic to teach (e.g., `Квадратні рівняння`)

All other fields (level, gaps, RAG context) are computed automatically by the graph nodes.

---

## Troubleshooting

### macOS Fork Safety Issues

If you encounter gRPC fork safety errors on macOS, the application automatically sets:
```
GRPC_ENABLE_FORK_SUPPORT=0
OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

### Missing Data Files

Ensure all required parquet files and embeddings are in the `data/` directory. The application will fail to start without them.
