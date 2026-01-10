# AI Tutor

Personalized learning platform powered by AI.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (optional)

### Option 1: Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Start all services
cd docker
docker-compose up
```

Services will be available at:
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
ai-tutor/
├── backend/          # FastAPI backend
│   ├── app/          # Application code
│   │   ├── api/      # API routes
│   │   ├── core/     # LangGraph workflows
│   │   ├── models/   # Pydantic models
│   │   ├── rag/      # RAG components
│   │   ├── services/ # Business logic
│   │   └── telemetry/# Observability
│   └── tests/        # Test suites
├── frontend/         # React frontend
│   └── src/
│       ├── api/      # API client
│       ├── components/
│       ├── pages/
│       └── types/
└── docker/           # Docker configuration
```

## Development

### Backend

```bash
cd backend
pytest                    # Run tests
ruff check .             # Lint code
ruff format .            # Format code
```

### Frontend

```bash
cd frontend
npm run lint             # Lint code
npm run build            # Build for production
```

## Environment Variables

See `.env.example` for all available configuration options.

## Team

- Mykhailo Rykhalskyi
- Denys Shcherbyna
- Mariia Hamaniuk
- Ostap Mnykh
- Maryna Ohinska
