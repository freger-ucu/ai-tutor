"""
Response Models

Pydantic models for API response serialization.
"""

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response model."""
    pass
