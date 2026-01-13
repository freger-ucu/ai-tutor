"""
API v1 Router

Aggregates all v1 API routers.
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.teacher import router as teacher_router
from app.api.v1.student import router as student_router
from app.api.v1.benchmark import router as benchmark_router
from app.api.v1.solver import router as solver_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(teacher_router, prefix="/teacher", tags=["teacher"])
api_router.include_router(student_router, prefix="/student", tags=["student"])
api_router.include_router(benchmark_router, prefix="/benchmark", tags=["benchmark"])
api_router.include_router(solver_router, tags=["solver"])
