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

## Configuration

Copy and edit the environment file:

```bash
cd backend
cp .env.example .env
```

Key settings in `.env`:

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | Main LLM provider (`openai`, `gemini`, `lapa`) |
| `OPENAI_API_KEY` | OpenAI API key (for complex reasoning tasks) |
| `OPENAI_MODEL` | OpenAI model (default: `gpt-4.1-mini`) |
| `LAPA_API_KEY` | Lapa API key (for simple tasks) |
| `TASK_PROVIDER_FEEDBACK` | Provider for feedback (`mamay`) |
| `TASK_PROVIDER_RECOMMENDATION` | Provider for recommendations (`mamay`) |

See `backend/.env.example` for all options.

## Data Files

The `backend/data/` directory is not included in the repository. Required files:

| File | Description |
|------|-------------|
| `benchmark_scores.parquet` | Student performance data |
| `benchmark_absences.parquet` | Attendance records |
| `embeddings/*.parquet` | Pre-computed textbook embeddings for RAG |

See [backend/README.md](backend/README.md) for detailed format specifications.

## Project Structure

```
ai-tutor/
├── backend/          # FastAPI + LangGraph backend
│   ├── app/          # Application code
│   ├── data/         # Runtime data (not in repo)
│   └── docs/         # Backend documentation
└── frontend/         # React frontend
```

## Documentation

- [Backend README](backend/README.md) - Detailed setup and API reference
- [Architecture](backend/docs/architecture.md) - Technical design
- [API Contracts](backend/docs/api-contracts.md) - Endpoint specifications
- [Business Value](backend/docs/business-value.md) - Feature descriptions

## Team

- Mykhailo Rykhalskyi
- Denys Shcherbyna
- Mariia Hamaniuk
- Ostap Mnykh
- Maryna Ohinska
