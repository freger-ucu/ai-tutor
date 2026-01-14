"""
Shared components for LangGraph flows.

Provides reusable nodes and utilities:
- rag_node: Configurable RAG retrieval node factory
- llm_node: LLM generation node factory with prompt building
- cpu_validators: Format and structure validation (no LLM calls)

NOTE: All imports are lazy to avoid grpcio mutex.cc crash on macOS.
"""

__all__ = [
    "create_rag_node",
    "RAGConfig",
    "create_llm_node",
    "LLMConfig",
    "validate_question_format",
    "validate_notes_format",
    "validate_json_structure",
    "ValidationError",
]


def __getattr__(name):
    """Lazy import to avoid grpcio crash on macOS."""
    if name in ("create_rag_node", "RAGConfig"):
        from .rag_node import create_rag_node, RAGConfig
        return create_rag_node if name == "create_rag_node" else RAGConfig
    elif name in ("create_llm_node", "LLMConfig"):
        from .llm_node import create_llm_node, LLMConfig
        return create_llm_node if name == "create_llm_node" else LLMConfig
    elif name in ("validate_question_format", "validate_notes_format", "validate_json_structure", "ValidationError"):
        from .cpu_validators import (
            validate_question_format,
            validate_notes_format,
            validate_json_structure,
            ValidationError,
        )
        return {
            "validate_question_format": validate_question_format,
            "validate_notes_format": validate_notes_format,
            "validate_json_structure": validate_json_structure,
            "ValidationError": ValidationError,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
