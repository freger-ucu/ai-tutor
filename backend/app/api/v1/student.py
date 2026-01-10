"""
Student API Endpoints

Handles student-facing functionality:
- Exercise generation
- Answer checking
- Personalized learning
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_student_dashboard():
    """TODO: Implement student dashboard endpoint."""
    raise NotImplementedError("Student dashboard not yet implemented")
