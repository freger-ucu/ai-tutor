"""
Health Check Endpoint

Provides health status of the API.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return health status of the API."""
    return {"status": "healthy"}
