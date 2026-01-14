"""
Agentic RAG Graph - V4 Enhanced Pipeline.

Single mode:
- V4 Enhanced: smart_retrieve → generate_answer → END (1 LLM call)

Enhancements:
- Ukrainian: Enhanced topic retrieval (5 topics, hybrid fallback)
- Algebra: Full worked examples (no truncation)
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

from .state import AgenticRAGState, SolverResult, create_initial_state
from .nodes.smart_retrieve import smart_retrieve_node
from .nodes.unified_generate import generate_answer_node


def build_v4_graph():
    """
    Build V4 Enhanced graph.

    Flow: smart_retrieve → generate_answer → END
    Total: 1 LLM call
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    graph = StateGraph(AgenticRAGState)

    graph.add_node("smart_retrieve", smart_retrieve_node)
    graph.add_node("generate_answer", generate_answer_node)

    graph.set_entry_point("smart_retrieve")
    graph.add_edge("smart_retrieve", "generate_answer")
    graph.add_edge("generate_answer", END)

    return graph.compile()


# Graph singleton
_v4_graph = None


def get_v4_graph():
    """Get singleton V4 Enhanced graph."""
    global _v4_graph
    if _v4_graph is None:
        _v4_graph = build_v4_graph()
    return _v4_graph


def reset_graphs():
    """Reset compiled graph."""
    global _v4_graph
    _v4_graph = None


# Backwards compatible aliases
def build_agentic_graph() -> StateGraph:
    """Build default graph (V4 Enhanced)."""
    return build_v4_graph()


def get_agentic_graph():
    """Get default graph (V4 Enhanced)."""
    return get_v4_graph()


def reset_graph():
    """Reset default graph."""
    reset_graphs()


async def solve_question(
    question: Dict[str, Any],
) -> SolverResult:
    """
    Solve a single question using V4 Enhanced pipeline.

    Args:
        question: Question dict with keys:
            - question_id
            - question_text
            - global_discipline_name (subject)
            - grade
            - answers
            - correct_answer_indices (optional)

    Returns:
        SolverResult with answer_index, confidence, reasoning, references
    """
    state = create_initial_state(question)
    graph = get_v4_graph()
    model_name = "agentic-rag-v4-enhanced"

    try:
        final_state = await graph.ainvoke(state)

        return SolverResult(
            answer_index=final_state.get("final_answer_index", 0),
            confidence=final_state.get("final_confidence", 0.5),
            reasoning=final_state.get("final_reasoning", ""),
            references=final_state.get("references", []),
            llm_calls=final_state.get("llm_calls_count", 0),
            model_used=model_name
        )

    except Exception as e:
        logger.error(f"solve_question failed: {e}", exc_info=True)
        return SolverResult(
            answer_index=0,
            confidence=0.1,
            reasoning=f"Error: {str(e)}",
            references=[],
            llm_calls=0,
            model_used=f"{model_name}-error"
        )


async def solve_question_with_state(
    question: Dict[str, Any],
) -> Dict[str, Any]:
    """Solve a question and return full state for debugging."""
    state = create_initial_state(question)
    graph = get_v4_graph()

    try:
        final_state = await graph.ainvoke(state)
        return dict(final_state)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


async def solve_question_smart(question: Dict[str, Any]) -> SolverResult:
    """
    Smart solver - uses V4 Enhanced for all subjects.

    All subjects use V4 Enhanced with subject-specific optimizations:
    - Ukrainian: Enhanced topic retrieval
    - Algebra: Full worked examples
    - History: Standard hybrid retrieval
    """
    return await solve_question(question)
