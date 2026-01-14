"""
LangGraph flow implementations.

Each flow is a separate subgraph with its own state type:
- notes: EP3.1 + EP3.2 (student/teacher notes generation)
- solver: EP7 (question solving with RAG)
- test_gen: EP4 (batch test generation with sample validation)
- check_answer: EP9 (open question answer checking)
- feedback: EP10 (test feedback generation)
- recommendation: EP6 (learning recommendations)

NOTE: All imports are lazy to avoid grpcio mutex.cc crash on macOS.
Import directly from submodules: from app.graph.flows.solver import solve_question
"""

# Lazy imports - import directly from submodules to avoid grpcio crash

__all__ = [
    # Notes flow (EP3.1, EP3.2)
    "notes_graph",
    "NotesState",
    "build_notes_graph",
    "get_notes_graph",
    # Solver flow (EP7)
    "solver_graph",
    "SolverState",
    "build_solver_graph",
    "get_solver_graph",
    # Test generation flow (EP4)
    "test_gen_graph",
    "TestGenState",
    "build_test_gen_graph",
    "get_test_gen_graph",
    "GenerationStats",
    # Check answer flow (EP9)
    "check_answer_graph",
    "CheckAnswerState",
    "build_check_answer_graph",
    "get_check_answer_graph",
    "CheckResult",
    # Feedback flow (EP10)
    "feedback_graph",
    "FeedbackState",
    "build_feedback_graph",
    "get_feedback_graph",
    "FeedbackResult",
    # Recommendation flow (EP6)
    "recommendation_graph",
    "RecommendationState",
    "build_recommendation_graph",
    "get_recommendation_graph",
    "RecommendationResult",
]


def __getattr__(name):
    """Lazy import of flow modules to avoid grpcio crash on macOS."""
    # Notes flow
    if name in ("notes_graph", "NotesState", "build_notes_graph", "get_notes_graph"):
        from . import notes
        return getattr(notes, name)
    # Solver flow
    elif name in ("solver_graph", "SolverState", "build_solver_graph", "get_solver_graph"):
        from . import solver
        return getattr(solver, name)
    # Test gen flow
    elif name in ("test_gen_graph", "TestGenState", "build_test_gen_graph", "get_test_gen_graph", "GenerationStats"):
        from . import test_gen
        return getattr(test_gen, name)
    # Check answer flow
    elif name in ("check_answer_graph", "CheckAnswerState", "build_check_answer_graph", "get_check_answer_graph", "CheckResult"):
        from . import check_answer
        return getattr(check_answer, name)
    # Feedback flow
    elif name in ("feedback_graph", "FeedbackState", "build_feedback_graph", "get_feedback_graph", "FeedbackResult"):
        from . import feedback
        return getattr(feedback, name)
    # Recommendation flow
    elif name in ("recommendation_graph", "RecommendationState", "build_recommendation_graph", "get_recommendation_graph", "RecommendationResult"):
        from . import recommendation
        return getattr(recommendation, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
