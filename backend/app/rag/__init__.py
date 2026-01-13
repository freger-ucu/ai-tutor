"""
Agentic RAG Solution for Ukrainian Educational Question Answering.

Simplified pipeline with 2-4 LLM calls maximum (vs 15+ in CRAG).
Target: 90%+ accuracy on lms_questions_dev.parquet benchmark.
"""

# Lazy imports to avoid loading heavy dependencies at import time
__all__ = [
    "solve_question",
    "build_agentic_graph",
    "AgenticRAGState",
    "SolverResult",
]


def __getattr__(name):
    """Lazy import for RAG components."""
    if name in ("solve_question", "build_agentic_graph"):
        from .graph import solve_question, build_agentic_graph
        globals()["solve_question"] = solve_question
        globals()["build_agentic_graph"] = build_agentic_graph
        return globals()[name]
    elif name in ("AgenticRAGState", "SolverResult"):
        from .state import AgenticRAGState, SolverResult
        globals()["AgenticRAGState"] = AgenticRAGState
        globals()["SolverResult"] = SolverResult
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
