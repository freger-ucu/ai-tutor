"""
Request Models

Pydantic models for API request validation.
"""

from pydantic import BaseModel


class BaseRequest(BaseModel):
    """Base request model."""
    pass
