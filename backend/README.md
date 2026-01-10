# AI Tutor Backend

FastAPI backend for the AI Tutor system.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   ├── core/         # LangGraph workflows
│   ├── models/       # Pydantic models
│   ├── rag/          # RAG components
│   ├── services/     # Business logic
│   └── telemetry/    # Observability
├── tests/            # Test suites
└── data/             # Runtime data (gitignored)
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp ../.env.example .env
```
