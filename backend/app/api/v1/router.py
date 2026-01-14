"""
API v1 Router

Aggregates all v1 API routers.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.teacher import solver_endpoint  # EP7 is a separate route
from app.api.v1.student import router as student_router
from app.api.v1.benchmark import router as benchmark_router
from app.api.v1.internal import router as internal_router
from app.models.requests import SolverRequest
from app.models.responses import SolverResponse

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
api_router.include_router(benchmark_router, prefix="/benchmark", tags=["benchmark"])
api_router.include_router(internal_router, tags=["internal"])

# EP7: Solver is at /solver (not under /teacher per architecture.md)
api_router.post("/solver", response_model=SolverResponse, tags=["solver"])(solver_endpoint)
