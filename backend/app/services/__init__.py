"""
Services Module

Business logic services for the AI Tutor system.
"""

from app.services.data_loader import (
    BenchmarkDataLoader,
    get_benchmark_loader,
    # Backwards-compatible aliases
    DataLoader,
    get_data_loader,
)

__all__ = [
    "BenchmarkDataLoader",
    "get_benchmark_loader",
    # Backwards-compatible aliases
    "DataLoader",
    "get_data_loader",
]
