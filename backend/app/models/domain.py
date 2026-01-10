"""
Domain Models

Core domain objects for the AI Tutor system.
"""

from pydantic import BaseModel


class Student(BaseModel):
    """Student domain model."""
    pass


class Exercise(BaseModel):
    """Exercise domain model."""
    pass


class Topic(BaseModel):
    """Topic domain model."""
    pass
