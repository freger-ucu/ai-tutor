"""
Check Answer Flow (EP9).

Evaluates a student's answer to an open-ended question using RAG.

Flow:
    retrieve_rag → evaluate_answer → format_response → END

Features:
- RAG retrieval for topic context
- LLM-based evaluation with constructive feedback
- Partial credit recognition
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.utils.json_parser import parse_json_response
from app.prompts.evaluator import (
    EVALUATOR_SYSTEM_PROMPT,
    build_evaluator_prompt,
)
from ..shared.rag_node import create_rag_node, RAGConfig

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class CheckAnswerState(TypedDict, total=False):
    """State for check answer flow."""

    # Input
    student_id: int
    subject: str
    grade: int
    topic: str
    subtopics: List[str]
    question: str
    student_answer: str

    # RAG output
    rag_context: str
    rag_references: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]

    # Evaluation output
    is_correct: bool
    feedback: str
    partial_credit: Optional[float]  # 0.0-1.0 for partial answers

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Graph Nodes
# =============================================================================

# Create RAG node for answer checking
_check_rag_node = create_rag_node(
    config=RAGConfig(
        max_chars=4000,
        top_k=4,
        include_references=False,
    ),
    query_key="query",  # We'll build query from topic + question
)


async def build_query_node(state: CheckAnswerState) -> Dict[str, Any]:
    """Build RAG query from topic and question."""
    topic = state.get("topic", "")
    question = state.get("question", "")
    query = f"{topic} {question}"
    return {"query": query}


async def retrieve_rag_node(state: CheckAnswerState) -> Dict[str, Any]:
    """Retrieve RAG context for the question."""
    logger.info(f"Retrieving context for: {state.get('topic', '')}")
    return await _check_rag_node(state)


@trace_chain(name="evaluate_answer")
async def evaluate_answer_node(state: CheckAnswerState) -> Dict[str, Any]:
    """
    Evaluate student's answer using LLM.

    Uses retrieved context to ground the evaluation.
    """
    client = get_llm_client()

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic = state.get("topic", "")
    subtopics = state.get("subtopics", [])
    question = state.get("question", "")
    student_answer = state.get("student_answer", "")
    context = state.get("rag_context", "")

    # Build evaluation prompt
    prompt = build_evaluator_prompt(
        subject=subject,
        grade=grade,
        topic=topic,
        subtopics=subtopics,
        question=question,
        student_answer=student_answer,
        context=context,
    )

    full_prompt = f"{EVALUATOR_SYSTEM_PROMPT}\n\n{prompt}"

    # Generate evaluation
    response = await client.generate(
        prompt=full_prompt,
        temperature=0.3,  # Lower temperature for consistent evaluation
        max_tokens=600,
    )

    # Parse response
    parsed = parse_json_response(
        response,
        fallback={"correct": False, "feedback": response},
        context="CheckAnswer",
    )

    is_correct = parsed.get("correct", False)
    feedback = parsed.get("feedback", response)

    # Handle various response formats
    if isinstance(is_correct, str):
        is_correct = is_correct.lower() in ("true", "yes", "так", "правильно")

    return {
        "is_correct": bool(is_correct),
        "feedback": str(feedback),
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


def format_response_node(state: CheckAnswerState) -> Dict[str, Any]:
    """Format final response (passthrough for now)."""
    return {}


# =============================================================================
# Build Graph
# =============================================================================


def build_check_answer_graph():
    """
    Build the LangGraph workflow for answer checking.

    Flow:
        build_query → retrieve_rag → evaluate_answer → format_response → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(CheckAnswerState)

    # Add nodes
    workflow.add_node("build_query", build_query_node)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("evaluate_answer", evaluate_answer_node)
    workflow.add_node("format_response", format_response_node)

    # Add edges
    workflow.set_entry_point("build_query")
    workflow.add_edge("build_query", "retrieve_rag")
    workflow.add_edge("retrieve_rag", "evaluate_answer")
    workflow.add_edge("evaluate_answer", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()


# Lazy graph compilation
_check_answer_graph = None


def get_check_answer_graph():
    """Get or create the compiled check answer graph (lazy initialization)."""
    global _check_answer_graph
    if _check_answer_graph is None:
        _check_answer_graph = build_check_answer_graph()
    return _check_answer_graph


# For backwards compatibility
check_answer_graph = None  # Will be set on first use


# =============================================================================
# Public API
# =============================================================================


class CheckResult:
    """Result from checking an open question answer."""

    def __init__(
        self,
        is_correct: bool,
        feedback: str,
        llm_calls: int = 0,
    ):
        self.is_correct = is_correct
        self.feedback = feedback
        self.llm_calls = llm_calls

    def to_dict(self) -> Dict[str, Any]:
        return {
            "correct": self.is_correct,
            "feedback": self.feedback,
            "llm_calls": self.llm_calls,
        }


async def check_open_answer(
    student_id: int,
    subject: str,
    grade: int,
    topic: str,
    subtopics: List[str],
    question: str,
    student_answer: str,
) -> CheckResult:
    """
    Check a student's open-ended answer using the LangGraph workflow.

    Args:
        student_id: Student identifier
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        topic: Main topic of the question
        subtopics: Specific subtopics covered
        question: The question text
        student_answer: Student's answer to evaluate

    Returns:
        CheckResult with is_correct, feedback
    """
    initial_state: CheckAnswerState = {
        "student_id": student_id,
        "subject": subject,
        "grade": grade,
        "topic": topic,
        "subtopics": subtopics,
        "question": question,
        "student_answer": student_answer,
        "rag_context": "",
        "rag_references": [],
        "retrieved_docs": [],
        "is_correct": False,
        "feedback": "",
        "partial_credit": None,
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_check_answer_graph()
        final_state = await graph.ainvoke(initial_state)
        return CheckResult(
            is_correct=final_state.get("is_correct", False),
            feedback=final_state.get("feedback", ""),
            llm_calls=final_state.get("llm_calls_count", 0),
        )
    except Exception as e:
        logger.error(f"Check answer failed: {e}", exc_info=True)
        return CheckResult(
            is_correct=False,
            feedback=f"Помилка оцінювання: {str(e)}",
            llm_calls=0,
        )
