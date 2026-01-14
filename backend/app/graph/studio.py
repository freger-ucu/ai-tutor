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


def test_gen_graph():
    """Build test generation graph (parallel architecture with planning).

    Flow:
        retrieve_context → plan_test → retrieve_concepts → batch_generate
                                                                ↓
                                                          batch_validate
                                                                ↓
                                                          prepare_retry ──┐
                                                                ↓         │
                                                            finalize ◄────┘

    Key features:
    - Planning phase: 1 LLM call to design entire test structure
    - Per-concept RAG: Parallel retrieval for each identified concept
    - Batch generation: All questions generated in parallel
    - Hybrid validation: MC reuses concept context, Open gets fresh RAG
    - Smart retry: Up to 2 retry iterations for failed questions

    Note: For Studio testing, recursion_limit=20 is sufficient.
    """
    from langgraph.graph import StateGraph, END
    from app.graph.flows.test_gen import (
        TestGenState,
        retrieve_context_node,
        plan_test_node,
        retrieve_concepts_node,
        batch_generate_node,
        batch_validate_node,
        prepare_retry_node,
        should_retry,
        finalize_node,
    )

    workflow = StateGraph(TestGenState)

    # Add nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("plan_test", plan_test_node)
    workflow.add_node("retrieve_concepts", retrieve_concepts_node)
    workflow.add_node("batch_generate", batch_generate_node)
    workflow.add_node("batch_validate", batch_validate_node)
    workflow.add_node("prepare_retry", prepare_retry_node)
    workflow.add_node("finalize", finalize_node)

    # Setup edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "plan_test")
    workflow.add_edge("plan_test", "retrieve_concepts")
    workflow.add_edge("retrieve_concepts", "batch_generate")
    workflow.add_edge("batch_generate", "batch_validate")
    workflow.add_edge("batch_validate", "prepare_retry")

    # Conditional retry loop
    workflow.add_conditional_edges(
        "prepare_retry",
        should_retry,
        {
            "batch_generate": "batch_generate",
            "finalize": "finalize",
        },
    )

    workflow.add_edge("finalize", END)
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
