"""
Recommendation Flow (EP6).

Generates teacher-facing recommendations about a student's performance.

Flow:
    prepare_data → generate_recommendation → format_response → END

Features:
- Analyzes student's strong and weak topics
- Considers missed lessons
- Provides actionable advice for teachers

Note: This flow does NOT use RAG (per design decision - current prompts work well).
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.prompts.recommendation import (
    RECOMMENDATION_SYSTEM_PROMPT,
    build_recommendation_prompt,
)

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class RecommendationState(TypedDict, total=False):
    """State for recommendation generation flow."""

    # Input
    student_id: int
    subject: str

    # Student data
    average_grade: float  # 0-12 scale
    level: str  # "weak" | "medium" | "strong"
    good_topics: List[str]  # Topics with score >= 10
    bad_topics: List[str]  # Topics with score < 6
    missed_topics: List[str]  # Topics from missed lessons

    # Output
    recommendation: str

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Graph Nodes
# =============================================================================


def prepare_data_node(state: RecommendationState) -> Dict[str, Any]:
    """
    Prepare and validate student data.

    This is a passthrough node for now, but could include
    data validation or enrichment in the future.
    """
    # Validate level
    level = state.get("level", "medium")
    if level not in ("weak", "medium", "strong"):
        level = "medium"

    # Ensure lists are not None
    good_topics = state.get("good_topics") or []
    bad_topics = state.get("bad_topics") or []
    missed_topics = state.get("missed_topics") or []

    logger.info(
        f"Preparing recommendation for student {state.get('student_id')}: "
        f"level={level}, avg={state.get('average_grade', 0):.1f}"
    )

    return {
        "level": level,
        "good_topics": good_topics,
        "bad_topics": bad_topics,
        "missed_topics": missed_topics,
    }


@trace_chain(name="generate_recommendation")
async def generate_recommendation_node(state: RecommendationState) -> Dict[str, Any]:
    """
    Generate teacher recommendation using LLM.

    Creates professional, actionable advice for teachers.
    """
    client = get_llm_client()

    subject = state.get("subject", "")
    average_grade = state.get("average_grade", 0.0)
    level = state.get("level", "medium")
    good_topics = state.get("good_topics", [])
    bad_topics = state.get("bad_topics", [])
    missed_topics = state.get("missed_topics", [])

    # Build prompt
    prompt = build_recommendation_prompt(
        subject=subject,
        average_grade=average_grade,
        level=level,
        good_topics=good_topics,
        bad_topics=bad_topics,
        missed_topics=missed_topics,
    )

    full_prompt = f"{RECOMMENDATION_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate recommendation
    response = await client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=800,
    )

    return {
        "recommendation": response,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


def format_response_node(state: RecommendationState) -> Dict[str, Any]:
    """Format final response (passthrough for now)."""
    return {}


# =============================================================================
# Build Graph
# =============================================================================


def build_recommendation_graph():
    """
    Build the LangGraph workflow for student recommendation.

    Flow:
        prepare_data → generate_recommendation → format_response → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(RecommendationState)

    # Add nodes
    workflow.add_node("prepare_data", prepare_data_node)
    workflow.add_node("generate_recommendation", generate_recommendation_node)
    workflow.add_node("format_response", format_response_node)

    # Add edges
    workflow.set_entry_point("prepare_data")
    workflow.add_edge("prepare_data", "generate_recommendation")
    workflow.add_edge("generate_recommendation", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()


# Lazy graph compilation
_recommendation_graph = None


def get_recommendation_graph():
    """Get or create the compiled recommendation graph (lazy initialization)."""
    global _recommendation_graph
    if _recommendation_graph is None:
        _recommendation_graph = build_recommendation_graph()
    return _recommendation_graph


# For backwards compatibility
recommendation_graph = None  # Will be set on first use


# =============================================================================
# Public API
# =============================================================================


class RecommendationResult:
    """Result from generating a student recommendation."""

    def __init__(
        self,
        recommendation: str,
        level: str,
        average_grade: float,
        llm_calls: int = 0,
    ):
        self.recommendation = recommendation
        self.level = level
        self.average_grade = average_grade
        self.llm_calls = llm_calls

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation": self.recommendation,
            "level": self.level,
            "average_grade": self.average_grade,
            "llm_calls": self.llm_calls,
        }


async def generate_student_recommendation(
    student_id: int,
    subject: str,
    average_grade: float,
    level: str,
    good_topics: Optional[List[str]] = None,
    bad_topics: Optional[List[str]] = None,
    missed_topics: Optional[List[str]] = None,
) -> RecommendationResult:
    """
    Generate a student recommendation using the LangGraph workflow.

    Args:
        student_id: Student identifier
        subject: Subject name (Алгебра, Українська мова, etc.)
        average_grade: Student's average grade (0-12)
        level: Student level (weak/medium/strong)
        good_topics: Topics with score >= 10
        bad_topics: Topics with score < 6
        missed_topics: Topics from missed lessons

    Returns:
        RecommendationResult with recommendation text
    """
    initial_state: RecommendationState = {
        "student_id": student_id,
        "subject": subject,
        "average_grade": average_grade,
        "level": level,
        "good_topics": good_topics or [],
        "bad_topics": bad_topics or [],
        "missed_topics": missed_topics or [],
        "recommendation": "",
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_recommendation_graph()
        final_state = await graph.ainvoke(initial_state)
        return RecommendationResult(
            recommendation=final_state.get("recommendation", ""),
            level=final_state.get("level", level),
            average_grade=average_grade,
            llm_calls=final_state.get("llm_calls_count", 0),
        )
    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}", exc_info=True)
        return RecommendationResult(
            recommendation=f"Помилка генерації рекомендації: {str(e)}",
            level=level,
            average_grade=average_grade,
            llm_calls=0,
        )
