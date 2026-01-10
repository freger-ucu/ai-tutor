"""
Benchmark API Endpoints

Handles evaluation and benchmarking functionality.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_benchmarks():
    """TODO: Implement benchmarks endpoint."""
    raise NotImplementedError("Benchmarks not yet implemented")
