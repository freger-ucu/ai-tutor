"""
Test Feedback Flow (EP10).

Generates AI feedback after a student completes a test.

Flow:
    aggregate_topics → generate_feedback → format_response → END

Features:
- Groups questions by topic/subtopic
- Performance analysis (correct/incorrect distribution)
- Constructive, motivating feedback for students

Note: This flow does NOT use RAG (per design decision - current prompts work well).
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.prompts.feedback import (
    FEEDBACK_SYSTEM_PROMPT,
    build_feedback_prompt,
)

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class QuestionResult(TypedDict):
    """Result for a single question."""

    question: str
    topic: str
    subtopics: List[str]
    correct: bool


class FeedbackState(TypedDict, total=False):
    """State for feedback generation flow."""

    # Input
    student_id: int
    subject: str
    questions: List[QuestionResult]

    # Aggregated data
    correct_count: int
    total_count: int
    score_percent: float
    incorrect_by_topic: Dict[str, List[str]]
    correct_by_topic: Dict[str, List[str]]

    # Output
    feedback: str

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Graph Nodes
# =============================================================================


def aggregate_topics_node(state: FeedbackState) -> Dict[str, Any]:
    """
    Aggregate questions by topic and count correct/incorrect.
    """
    questions = state.get("questions", [])

    correct_count = 0
    total_count = len(questions)
    incorrect_by_topic: Dict[str, List[str]] = {}
    correct_by_topic: Dict[str, List[str]] = {}

    for q in questions:
        # Build topic key including subtopics if present
        topic = q.get("topic", "Unknown")
        subtopics = q.get("subtopics", [])

        if subtopics:
            topic_key = f"{topic} > {', '.join(subtopics)}"
        else:
            topic_key = topic

        question_text = q.get("question", "")

        if q.get("correct", False):
            correct_count += 1
            if topic_key not in correct_by_topic:
                correct_by_topic[topic_key] = []
            correct_by_topic[topic_key].append(question_text)
        else:
            if topic_key not in incorrect_by_topic:
                incorrect_by_topic[topic_key] = []
            incorrect_by_topic[topic_key].append(question_text)

    score_percent = (correct_count / total_count * 100) if total_count > 0 else 0

    logger.info(
        f"Aggregated {total_count} questions: {correct_count} correct ({score_percent:.0f}%)"
    )

    return {
        "correct_count": correct_count,
        "total_count": total_count,
        "score_percent": score_percent,
        "incorrect_by_topic": incorrect_by_topic,
        "correct_by_topic": correct_by_topic,
    }


@trace_chain(name="generate_feedback")
async def generate_feedback_node(state: FeedbackState) -> Dict[str, Any]:
    """
    Generate feedback using LLM.

    Creates constructive, motivating feedback based on test performance.
    """
    client = get_llm_client()

    subject = state.get("subject", "")
    correct_count = state.get("correct_count", 0)
    total_count = state.get("total_count", 0)
    incorrect_by_topic = state.get("incorrect_by_topic", {})
    correct_by_topic = state.get("correct_by_topic", {})

    # Build prompt
    prompt = build_feedback_prompt(
        subject=subject,
        correct_count=correct_count,
        total_count=total_count,
        incorrect_by_topic=incorrect_by_topic,
        correct_by_topic=correct_by_topic,
    )

    full_prompt = f"{FEEDBACK_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate feedback
    response = await client.generate(
        prompt=full_prompt,
        temperature=0.7,
        max_tokens=1500,
    )

    return {
        "feedback": response,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


def format_response_node(state: FeedbackState) -> Dict[str, Any]:
    """Format final response (passthrough for now)."""
    return {}


# =============================================================================
# Build Graph
# =============================================================================


def build_feedback_graph():
    """
    Build the LangGraph workflow for test feedback.

    Flow:
        aggregate_topics → generate_feedback → format_response → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(FeedbackState)

    # Add nodes
    workflow.add_node("aggregate_topics", aggregate_topics_node)
    workflow.add_node("generate_feedback", generate_feedback_node)
    workflow.add_node("format_response", format_response_node)

    # Add edges
    workflow.set_entry_point("aggregate_topics")
    workflow.add_edge("aggregate_topics", "generate_feedback")
    workflow.add_edge("generate_feedback", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()


# Lazy graph compilation
_feedback_graph = None


def get_feedback_graph():
    """Get or create the compiled feedback graph (lazy initialization)."""
    global _feedback_graph
    if _feedback_graph is None:
        _feedback_graph = build_feedback_graph()
    return _feedback_graph


# For backwards compatibility
feedback_graph = None  # Will be set on first use


# =============================================================================
# Public API
# =============================================================================


class FeedbackResult:
    """Result from generating test feedback."""

    def __init__(
        self,
        feedback: str,
        correct_count: int,
        total_count: int,
        score_percent: float,
        llm_calls: int = 0,
    ):
        self.feedback = feedback
        self.correct_count = correct_count
        self.total_count = total_count
        self.score_percent = score_percent
        self.llm_calls = llm_calls

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback": self.feedback,
            "correct_count": self.correct_count,
            "total_count": self.total_count,
            "score_percent": self.score_percent,
            "llm_calls": self.llm_calls,
        }


async def generate_test_feedback(
    student_id: int,
    subject: str,
    questions: List[Dict[str, Any]],
) -> FeedbackResult:
    """
    Generate test feedback using the LangGraph workflow.

    Args:
        student_id: Student identifier
        subject: Subject name (Алгебра, Українська мова, etc.)
        questions: List of question results with:
            - question: str
            - topic: str
            - subtopics: List[str]
            - correct: bool

    Returns:
        FeedbackResult with feedback text and statistics
    """
    initial_state: FeedbackState = {
        "student_id": student_id,
        "subject": subject,
        "questions": questions,
        "correct_count": 0,
        "total_count": 0,
        "score_percent": 0.0,
        "incorrect_by_topic": {},
        "correct_by_topic": {},
        "feedback": "",
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_feedback_graph()
        final_state = await graph.ainvoke(initial_state)
        return FeedbackResult(
            feedback=final_state.get("feedback", ""),
            correct_count=final_state.get("correct_count", 0),
            total_count=final_state.get("total_count", 0),
            score_percent=final_state.get("score_percent", 0.0),
            llm_calls=final_state.get("llm_calls_count", 0),
        )
    except Exception as e:
        logger.error(f"Feedback generation failed: {e}", exc_info=True)
        return FeedbackResult(
            feedback=f"Помилка генерації зворотного зв'язку: {str(e)}",
            correct_count=0,
            total_count=len(questions),
            score_percent=0.0,
            llm_calls=0,
        )
