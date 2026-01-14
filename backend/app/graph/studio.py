"""
LangGraph Studio entry point.

Exports graph builder functions for use with LangGraph Studio local development.
Run with: langgraph dev
"""

import os

# Set environment variables before any imports
os.environ.setdefault("GRPC_ENABLE_FORK_SUPPORT", "0")
os.environ.setdefault("OBJC_DISABLE_INITIALIZE_FORK_SAFETY", "YES")


def notes_graph():
    """Build notes generation graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.notes import (
        NotesState,
        analyze_students_node,
        collect_gaps_node,
        retrieve_rag_node,
        generate_notes_node,
    )

    workflow = StateGraph(NotesState)
    workflow.add_node("analyze_students", analyze_students_node)
    workflow.add_node("collect_gaps", collect_gaps_node)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_notes", generate_notes_node)
    workflow.set_entry_point("analyze_students")
    workflow.add_edge("analyze_students", "collect_gaps")
    workflow.add_edge("collect_gaps", "retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_notes")
    workflow.add_edge("generate_notes", END)
    return workflow


def solver_graph():
    """Build solver graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.solver import (
        SolverState,
        retrieve_rag_node,
        solve_question_node,
    )

    workflow = StateGraph(SolverState)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("solve_question", solve_question_node)
    workflow.set_entry_point("retrieve_rag")
    workflow.add_edge("retrieve_rag", "solve_question")
    workflow.add_edge("solve_question", END)
    return workflow


def test_gen_graph():
    """Build test generation graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.test_gen import (
        TestGenState,
        retrieve_rag_node,
        generate_batch_node,
        validate_batch_node,
        should_continue,
    )

    workflow = StateGraph(TestGenState)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_batch", generate_batch_node)
    workflow.add_node("validate_batch", validate_batch_node)
    workflow.set_entry_point("retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_batch")
    workflow.add_edge("generate_batch", "validate_batch")
    workflow.add_conditional_edges("validate_batch", should_continue, {"continue": "generate_batch", "end": END})
    return workflow


def check_answer_graph():
    """Build check answer graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.check_answer import (
        CheckAnswerState,
        retrieve_rag_node,
        evaluate_answer_node,
    )

    workflow = StateGraph(CheckAnswerState)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("evaluate_answer", evaluate_answer_node)
    workflow.set_entry_point("retrieve_rag")
    workflow.add_edge("retrieve_rag", "evaluate_answer")
    workflow.add_edge("evaluate_answer", END)
    return workflow


def feedback_graph():
    """Build feedback graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.feedback import (
        FeedbackState,
        retrieve_rag_node,
        generate_feedback_node,
    )

    workflow = StateGraph(FeedbackState)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.set_entry_point("retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_feedback")
    workflow.add_edge("generate_feedback", END)
    return workflow


def recommendation_graph():
    """Build recommendation graph."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.recommendation import (
        RecommendationState,
        analyze_performance_node,
        generate_recommendation_node,
    )

    workflow = StateGraph(RecommendationState)
    workflow.add_node("analyze_performance", analyze_performance_node)
    workflow.add_node("generate_recommendation", generate_recommendation_node)
    workflow.set_entry_point("analyze_performance")
    workflow.add_edge("analyze_performance", "generate_recommendation")
    workflow.add_edge("generate_recommendation", END)
    return workflow
