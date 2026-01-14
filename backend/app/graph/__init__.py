"""
LangGraph-based workflow orchestration.

This module provides unified graph implementations for all AI Tutor workflows.
Each flow is a separate subgraph with its own state type, enabling:
- Clean separation of concerns
- Easy testing in isolation
- Full LangSmith tracing per operation

Architecture:
- shared/: Reusable nodes (RAG retrieval, LLM generation, validators)
- flows/: Individual subgraphs for each endpoint group

Flows:
- notes: EP3.1 + EP3.2 (student/teacher notes generation)
- test_gen: EP4 (batch test generation with sample validation)
- check_answer: EP9 (open question answer checking)
- feedback: EP10 (test feedback generation)
- recommendation: EP6 (learning recommendations)

NOTE: All imports are lazy to avoid grpcio mutex.cc crash on macOS.
Import directly from submodules: from app.graph.flows.notes import generate_notes
"""

# Lazy imports to avoid grpcio initialization at package load (macOS mutex.cc issue)
# Import directly from submodules instead: from app.graph.flows.notes import generate_notes

__all__ = [
    # Graphs
    "notes_graph",
    "test_gen_graph",
    "check_answer_graph",
    "feedback_graph",
    "recommendation_graph",
    # States (for type hints)
    "NotesState",
    "TestGenState",
    "CheckAnswerState",
    "FeedbackState",
    "RecommendationState",
    # Result classes
    "GenerationStats",
    "CheckResult",
    "FeedbackResult",
    "RecommendationResult",
]


def __getattr__(name):
    """Lazy import of flow modules to avoid grpcio crash on macOS."""
    if name in ("notes_graph", "NotesState"):
        from .flows.notes import notes_graph, NotesState
        return notes_graph if name == "notes_graph" else NotesState
    elif name in ("test_gen_graph", "TestGenState", "GenerationStats"):
        from .flows.test_gen import test_gen_graph, TestGenState, GenerationStats
        if name == "test_gen_graph":
            return test_gen_graph
        elif name == "TestGenState":
            return TestGenState
        else:
            return GenerationStats
    elif name in ("check_answer_graph", "CheckAnswerState", "CheckResult"):
        from .flows.check_answer import check_answer_graph, CheckAnswerState, CheckResult
        if name == "check_answer_graph":
            return check_answer_graph
        elif name == "CheckAnswerState":
            return CheckAnswerState
        else:
            return CheckResult
    elif name in ("feedback_graph", "FeedbackState", "FeedbackResult"):
        from .flows.feedback import feedback_graph, FeedbackState, FeedbackResult
        if name == "feedback_graph":
            return feedback_graph
        elif name == "FeedbackState":
            return FeedbackState
        else:
            return FeedbackResult
    elif name in ("recommendation_graph", "RecommendationState", "RecommendationResult"):
        from .flows.recommendation import recommendation_graph, RecommendationState, RecommendationResult
        if name == "recommendation_graph":
            return recommendation_graph
        elif name == "RecommendationState":
            return RecommendationState
        else:
            return RecommendationResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
