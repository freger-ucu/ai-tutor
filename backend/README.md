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

Create a `.env` file in the `backend` directory:

```bash
# LLM Configuration
LLM_API_KEY=your-api-key
LLM_BASE_URL=http://your-llm-endpoint
LLM_MODEL=your-model-name

# Or use OpenAI
# LLM_API_KEY=sk-your-openai-key
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=mamay

# Phoenix Telemetry (optional - LLM Observability)
PHOENIX_ENABLED=false
PHOENIX_ENDPOINT=

# LangSmith Tracing (optional)
LANGSMITH_ENABLED=false
LANGSMITH_API_KEY=your-langsmith-key
LANGSMITH_PROJECT=ai-tutor
```

### 4. Prepare Data Files

Ensure the following data files are present in the `data/` directory:

```
data/
├── benchmark_scores.parquet    # Student performance data
├── benchmark_absences.parquet  # Attendance records
└── embeddings/                 # Pre-computed vector embeddings (for RAG)
```

The `embeddings/`, `toc/`, and `pages/` folders contain textbook data used by the RAG system to ground AI responses in official curriculum content.

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

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_KEY` | - | API key for LLM provider |
| `LLM_BASE_URL` | `http://146.59.127.106:4000` | LLM API endpoint |
| `LLM_MODEL` | `mamay` | Model name to use |
| `LLM_TEMPERATURE` | `0.0` | Generation temperature |
| `LLM_MAX_TOKENS` | `500` | Max output tokens |
| `BACKEND_PORT` | `8000` | Server port |
| `DEBUG` | `true` | Debug mode |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `PHOENIX_ENABLED` | `false` | Enable Phoenix telemetry |
| `LANGSMITH_ENABLED` | `false` | Enable LangSmith tracing |

## API Endpoints Overview

### Teacher Endpoints (EP1-EP7)
- `GET /api/v1/teacher/topics` - List available topics
- `GET /api/v1/teacher/students` - Get students for a class
- `POST /api/v1/teacher/notes` - Generate lesson notes
- `POST /api/v1/teacher/test` - Generate test questions
- `GET /api/v1/teacher/students/{id}/report` - Student performance report
- `POST /api/v1/teacher/students/{id}/recommendation` - Get teaching recommendations
- `POST /api/v1/teacher/solve` - Solve a question with RAG

### Student Endpoints (EP8-EP10)
- `POST /api/v1/student/explain` - Explain a concept
- `POST /api/v1/student/check-answer` - Evaluate an answer
- `POST /api/v1/student/feedback` - Get test feedback

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

| Graph | Description |
|-------|-------------|
| notes | Generate lesson notes with prerequisite-aware recap |
| test_gen | Generate validated test questions with planning-based parallel architecture |
| check_answer | Evaluate student answers |
| feedback | Generate test feedback |
| recommendation | Generate teaching recommendations |

### Test Gen Graph Input

The test_gen graph uses a planning-based architecture with 7 nodes:
1. **retrieve_context** - Get base topic context from RAG
2. **plan_test** - LLM plans test structure (concepts, question specs)
3. **retrieve_concepts** - Parallel RAG retrieval for each concept
4. **batch_generate** - Parallel question generation (10 concurrent)
5. **batch_validate** - CPU + LLM validation (format checks, then content validation)
6. **prepare_retry** - Queue failed specs for retry (max 2 iterations)
7. **finalize** - Log stats and return validated questions

Input fields:
- `subject`: Subject name (`Алгебра`, `Українська мова`, `Історія України`)
- `grade`: Grade level (`8` or `9`)
- `topic_definition`: Topic for the test
- `easy_count`, `medium_count`, `hard_count`: Number of questions per difficulty

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

### Redis Connection Errors

Redis is optional. If not available, caching will be disabled. To install Redis:
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
```
