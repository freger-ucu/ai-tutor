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
        retrieve_context → plan_test (assigns difficulty) → batch_generate
                                                                   ↓
                                                             batch_validate
                                                                   ↓
                                                             prepare_retry ──┐
                                                                   ↓         │
                                                           finalize (sort) ◄─┘

    Key features:
    - Planning phase: 1 LLM call to design 12 question specs with focus areas
    - CPU-based difficulty: Assigned at planning based on student level
      - weak: 6 easy, 4 medium, 2 hard
      - medium: 4 easy, 4 medium, 4 hard
      - strong: 2 easy, 4 medium, 6 hard
    - Level-aware generation: Prompts adjusted based on student level and difficulty
    - Topic-level RAG: Single retrieval used for all questions
    - Batch generation: All questions generated in parallel
    - Hybrid validation: CPU format check + LLM solver-based correctness
    - Smart retry: Only retry if 3+ fail, max 1 retry iteration
    - Output sorted: easy first, then medium, then hard

    Note: For Studio testing, recursion_limit=20 is sufficient.
    """
    from langgraph.graph import StateGraph, END
    from app.graph.flows.test_gen import (
        TestGenState,
        retrieve_context_node,
        plan_test_node,
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
    workflow.add_node("batch_generate", batch_generate_node)
    workflow.add_node("batch_validate", batch_validate_node)
    workflow.add_node("prepare_retry", prepare_retry_node)
    workflow.add_node("finalize", finalize_node)

    # Setup edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "plan_test")
    workflow.add_edge("plan_test", "batch_generate")
    workflow.add_edge("batch_generate", "batch_validate")
    workflow.add_edge("batch_validate", "prepare_retry")

    # Conditional retry loop - goes to finalize when done
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
    """Build feedback graph (EP10 - no RAG)."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.feedback import (
        FeedbackState,
        aggregate_topics_node,
        generate_feedback_node,
    )

    workflow = StateGraph(FeedbackState)
    workflow.add_node("aggregate_topics", aggregate_topics_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.set_entry_point("aggregate_topics")
    workflow.add_edge("aggregate_topics", "generate_feedback")
    workflow.add_edge("generate_feedback", END)
    return workflow


def recommendation_graph():
    """Build recommendation graph (EP6 - no RAG)."""
    from langgraph.graph import StateGraph, END
    from app.graph.flows.recommendation import (
        RecommendationState,
        prepare_data_node,
        generate_recommendation_node,
    )

    workflow = StateGraph(RecommendationState)
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("generate_recommendation", generate_recommendation_node)
    workflow.set_entry_point("prepare_data")
    workflow.add_edge("prepare_data", "generate_recommendation")
    workflow.add_edge("generate_recommendation", END)
    return workflow
