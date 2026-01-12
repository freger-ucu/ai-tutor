# AI Tutor

Personalized learning platform for Ukrainian schools. Helps teachers prepare lessons and tests adapted to student performance levels.

## Features

- **Teacher Flow**: Analyze class performance, generate lessons, create personalized tests by student level (weak/medium/strong)
- **Student Flow**: Take tests, view results, get personalized learning recommendations
- **Clustering**: Automatic grouping of students by performance using quartile-based algorithm
- **Ukrainian Curriculum**: Built for Ukrainian school system (grades 8-9, 12-point scale)

## Current Status

| Component | Status | Description |
|-----------|--------|-------------|
| DataLoader | Done | Loads student/teacher data from parquet files |
| Pydantic Models | Done | Type-safe request/response models |
| Config + Health | Done | App configuration, health endpoints |
| Clustering Service | Done | Groups students by performance level |
| Student API | Done | Stub endpoints (mock data) |
| Teacher API | Done | Stub endpoints (mock data) |
| Topic Routing | Pending | AI-based topic analysis |
| LLM Integration | Pending | Connect to real AI services |

**Tests**: 238 passing

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (for frontend)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

API available at http://localhost:8000/docs

### Run Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
ai-tutor/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   │   ├── health.py    # Health checks
│   │   │   ├── student.py   # Student endpoints
│   │   │   └── teacher.py   # Teacher endpoints
│   │   ├── models/          # Pydantic models
│   │   │   ├── domain.py    # Business objects
│   │   │   ├── enums.py     # Enumerations
│   │   │   ├── requests.py  # API requests
│   │   │   └── responses.py # API responses
│   │   ├── services/        # Business logic
│   │   │   ├── clustering.py   # Student clustering
│   │   │   └── data_loader.py  # Data access
│   │   ├── config.py        # Settings
│   │   └── main.py          # FastAPI app
│   ├── data/                # Data files (not in repo)
│   ├── docs/                # Documentation
│   └── tests/               # Test suites
├── frontend/                # React frontend
└── docker/                  # Docker configuration
```

## Data

Data files are not included in the repository. Place them in `backend/data/`:

```
backend/data/
├── benchmark_scores.parquet    # Student grades
└── benchmark_absences.parquet  # Student absences
```

See `backend/docs/data_schema.md` for data format details.

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe

### Student
- `GET /api/v1/student/{id}/test?test_id=X` - Get test exercises
- `POST /api/v1/student/submit` - Submit answers
- `GET /api/v1/student/{id}/result/{test_id}` - Get results
- `GET /api/v1/student/{id}/summary/{test_id}` - Get personalized summary

### Teacher
- `POST /api/v1/teacher/analyze-class` - Analyze class performance
- `POST /api/v1/teacher/generate-lesson` - Generate lesson content
- `POST /api/v1/teacher/generate-test-pool` - Generate exercise pool
- `POST /api/v1/teacher/create-personalized-tests` - Create tests per cluster
- `POST /api/v1/teacher/generate-report` - Generate class report
- `POST /api/v1/teacher/full-pipeline` - Run complete workflow

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables:
- `DATA_DIR` - Path to data directory
- `LLM_API_KEY` - API key for LLM provider
- `REDIS_URL` - Redis connection URL

## Documentation

- `backend/docs/implementation_status.md` - Detailed implementation status
- `backend/docs/data_schema.md` - Data format specification
- `backend/docs/api_flow_and_contracts.md` - API contracts

## Team

- Mykhailo Rykhalskyi
- Denys Shcherbyna
- Mariia Hamaniuk
- Ostap Mnykh
- Maryna Ohinska
