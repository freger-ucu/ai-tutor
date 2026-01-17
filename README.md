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
cp .env.example .env      # Configure your API keys
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
