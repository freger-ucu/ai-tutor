# AI Tutor

Personalized learning platform for Ukrainian schools. Helps teachers prepare lessons and tests adapted to student performance levels, powered by AI with RAG-grounded responses.

## Features

- **Teacher Tools**: Generate lesson notes, create tests, get student recommendations
- **Student Tools**: Get answer feedback, concept explanations, test analysis
- **RAG System**: AI responses grounded in official Ukrainian textbooks
- **Multi-subject**: Algebra, Ukrainian Language, Ukrainian History (Grades 8-9)

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend)
- Redis (for caching)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Redis Setup

```bash
# Using Docker (recommended)
docker run -d -p 6379:6379 redis:latest

# Or install locally
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
```

## Project Structure

```
ai-tutor/
├── backend/          # FastAPI + LangGraph backend
│   ├── app/          # Application code
│   ├── data/         # Runtime data (not in repo)
│   └── docs/         # Backend documentation
└── frontend/         # React frontend
```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4-turbo-preview

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application
DEBUG=true
LOG_LEVEL=INFO

# Caching TTL (seconds)
CACHE_TTL_LESSON_TEMPLATE=86400
CACHE_TTL_CLASS_CLUSTERS=3600
```

## System Requirements

### Backend Dependencies

| Category | Package | Version |
|----------|---------|---------|
| Core | fastapi | >=0.109.0 |
| | uvicorn[standard] | >=0.27.0 |
| | pydantic | >=2.5.0 |
| | pydantic-settings | >=2.1.0 |
| | python-dotenv | >=1.0.0 |
| Data Processing | pandas | >=2.1.0 |
| | numpy | >=1.26.0 |
| | pyarrow | >=14.0.0 |
| LLM & AI | openai | >=1.10.0 |
| | langchain | >=0.1.0 |
| | langchain-core | >=0.3.0 |
| | langgraph | >=0.2.0 |
| RAG | rank-bm25 | >=0.2.2 |
| | sentence-transformers | >=2.2.0 |
| | pymorphy2 | >=0.9.0 |
| | pymorphy2-dicts-uk | >=2.4.0 |
| Caching | redis | >=5.0.0 |
| Telemetry | arize-phoenix | >=4.0.0 |
| | openinference-instrumentation-openai | >=0.1.0 |
| | opentelemetry-sdk | >=1.20.0 |
| | langsmith | >=0.1.0 |
| HTTP Client | httpx | >=0.26.0 |
| Development | pytest | >=7.4.0 |
| | pytest-asyncio | >=0.23.0 |
| | pytest-cov | >=4.1.0 |
| | ruff | >=0.1.0 |

### Frontend Dependencies

| Package | Version |
|---------|---------|
| react | ^19.2.0 |
| react-dom | ^19.2.0 |
| react-router-dom | ^7.12.0 |
| tailwindcss | ^4.1.18 |
| @tailwindcss/vite | ^4.1.18 |
| katex | ^0.16.27 |
| typescript | ~5.9.3 |
| vite | ^7.2.4 |
| @vitejs/plugin-react | ^5.1.1 |

## Data Requirements

The system expects the following data files in the `backend/data/` directory:

### Benchmark Data

**benchmark_scores.parquet**
```
Columns: student_id, class_id, subject, topic_id, topic, score, date
Format: Parquet
Description: Historical student grades across all subjects and topics
```

**benchmark_absences.parquet**
```
Columns: student_id, class_id, subject, topic_id, topic, date
Format: Parquet
Description: Student attendance records linked to specific topics
```

### Curriculum Structure

**data/toc/** - Table of Contents files defining curriculum structure
```json
{
  "algebra": [
    {
      "id": "alg_8_quad_eq",
      "name": "Quadratic Equations",
      "grade": 8,
      "prerequisites": ["alg_8_linear_eq"],
      "page_ranges": ["page_45", "page_46"],
      "subtopics": [...]
    }
  ]
}
```

**data/pages/** - Textbook content in Markdown format

**data/embeddings/** - Pre-computed embeddings for RAG retrieval

## API Endpoints

### Teacher API

```
POST /api/v1/teacher/analyze-class
    - Analyze student performance and cluster by ability level
    - Input: class_id, subject, topic
    - Output: class insights, cluster assignments, topic routing

POST /api/v1/teacher/generate-lesson
    - Generate personalized lesson plan with difficulty-adjusted examples
    - Input: class_id, subject, topic_id, class_insights
    - Output: lesson content, control questions, sources

POST /api/v1/teacher/generate-test-pool
    - Create pool of validated test questions
    - Input: topic_id, subject, grade, pool_size
    - Output: exercise pool with validation report

POST /api/v1/teacher/create-personalized-tests
    - Assign personalized tests to students based on clusters
    - Input: pool_id, cluster_assignments
    - Output: tests by cluster, student assignments

POST /api/v1/teacher/generate-post-test-report
    - Generate analytics report after test completion
    - Input: class_id, test_id, student_results
    - Output: statistics, problem topics, recommendations
```

### Student API

```
GET /api/v1/student/get-test/{student_id}
    - Retrieve personalized test for student
    - Output: test_id, exercises, time_limit

POST /api/v1/student/submit-answers
    - Submit test answers for grading
    - Input: student_id, test_id, answers
    - Output: submission_id, status

GET /api/v1/student/get-results/{submission_id}
    - Get test results and performance metrics
    - Output: score, correct/incorrect breakdown, error patterns

GET /api/v1/student/get-summary/{submission_id}
    - Get personalized learning summary
    - Output: result analysis, topics to review, practice exercises
```

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/teacher/analyze-class" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": "8-A",
    "subject": "algebra",
    "topic": "Quadratic Equations"
  }'
```

## Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test module
pytest tests/test_api/test_teacher.py

# Run with verbose output
pytest -v
```

## Architecture Overview

The system uses a multi-stage LangGraph state machine with RAG pipeline:

**Teacher Flow:**
1. Student Clustering - Quartile-based grouping by performance
2. Class Analysis - Identify weak topics and attendance gaps
3. Topic Routing - Match query to curriculum structure
4. Hybrid Retrieval - BM25 + Vector search with RRF fusion
5. Lesson Generation - Create difficulty-adjusted content
6. Test Generation - Produce and validate question pool
7. Test Personalization - Assign questions by student cluster

**Student Flow:**
1. Test Assignment - Deliver cluster-appropriate questions
2. Answer Checking - Automated grading with error analysis
3. Pattern Recognition - Identify recurring mistake types
4. Summary Generation - Create personalized review materials

**Key Technologies:**
- **RAG Pipeline**: Hybrid search (BM25 + Vector) with Reciprocal Rank Fusion
- **State Management**: LangGraph for complex workflow orchestration
- **Validation**: Automated solver verification of generated questions
- **Caching**: Redis for template and cluster result optimization
- **Monitoring**: Arize Phoenix for LLM tracing and cost tracking

## Performance

**Token Usage (per class, with optimization):**
- RAG Context: ~1,500 tokens (70% reduction)
- Teacher Lesson: ~1,200 tokens (template + delta)
- Test Pool Generation: ~2,000 tokens
- Test Personalization: ~500 tokens
- Answer Checking: ~5,000 tokens (batch processing)
- Student Summary: ~1,000 tokens
- Teacher Report: ~1,500 tokens
- **Total**: ~12,700 tokens (60% optimization vs baseline)

**Cache Performance:**
- Hit Rate: 60-70% on repeated queries
- Lesson Template TTL: 24 hours
- Cluster Cache TTL: 1 hour

**Response Times:**
- Class Analysis: 3-5 seconds
- Lesson Generation: 8-12 seconds
- Test Pool Creation: 15-20 seconds
- Answer Grading: 2-3 seconds per student

## Troubleshooting

**Redis Connection Failed:**
```bash
# Verify Redis is running
redis-cli ping
# Expected output: PONG

# Check Redis logs
docker logs <redis-container-id>
```

**Import Errors:**
```bash
# Clear and reinstall dependencies
pip cache purge
pip install -r requirements.txt --force-reinstall
```

**Port Already in Use:**
```bash
# Backend - change port
uvicorn app.main:app --port 8001

# Frontend - edit vite.config.ts
export default defineConfig({
  server: { port: 5174 }
})
```

**LLM API Rate Limits:**
```bash
# Check your API key quota
# Add rate limiting in .env
RATE_LIMIT_PER_MINUTE=60
```

## Documentation

See [backend/README.md](backend/README.md) for detailed setup and API reference.

- [Architecture](backend/docs/architecture.md) - Technical design
- [API Contracts](backend/docs/api-contracts.md) - Endpoint specifications
- [Business Value](backend/docs/business-value.md) - Feature descriptions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Team

- Mykhailo Rykhalskyi
- Denys Shcherbyna
- Mariia Hamaniuk
- Ostap Mnykh
- Maryna Ohinska

## Contributing

Contributions are welcome. Please ensure all tests pass before submitting pull requests.

```bash
# Run tests before committing
pytest
npm run lint

# Format code
ruff format .
```

## Status

**Current Version**: 0.1.0-demo

**Roadmap:**
- Multi-language UI support (Ukrainian, English)
- Real-time collaboration features
- Mobile application
- LMS platform integrations
- Advanced analytics dashboard
