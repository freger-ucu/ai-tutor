"""
Solver API Endpoint (Endpoint 7)
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SolverRequest(BaseModel):
    """Request with questions to solve."""
    questions: list[str]


class SolverAnswer(BaseModel):
    """Solved question with explanation."""
    question: str
    answer_explained: str


class SolverResponse(BaseModel):
    """Solver response."""
    solutions: list[SolverAnswer]


@router.post("/solver", response_model=SolverResponse)
async def solve_questions(request: SolverRequest) -> SolverResponse:
    """Solve questions and return explanations."""
    solutions = []
    for question in request.questions:
        solutions.append(
            SolverAnswer(
                question=question,
                answer_explained=(
                    "Рішення сформовано як загальний приклад. "
                    "Деталізуйте запит для точнішої відповіді."
                ),
            )
        )
    return SolverResponse(solutions=solutions)
