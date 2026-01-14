"""
Solver Flow (EP7).

Solves multiple-choice questions using RAG-enhanced generation.

Flow:
    retrieve_rag → generate_answer → END

Features:
- Subject-specific expert prompts
- RAG context retrieval
- Confidence scoring
- Source reference tracking

This is essentially a wrapper around the existing RAG pipeline,
but with LangGraph structure for consistency and tracing.
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import generate_json_safe
from app.rag.nodes.unified_generate import (
    SUBJECT_PROMPTS,
    DEFAULT_PROMPT,
    _format_options,
)
from ..shared.rag_node import create_rag_node, RAGConfig

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class SolverState(TypedDict, total=False):
    """State for solver flow."""

    # Input
    question_id: str
    question_text: str
    subject: str
    grade: int
    answers: List[str]
    correct_indices: List[int]  # For evaluation only

    # RAG output
    rag_context: str
    rag_references: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    matched_topics: List[Dict[str, Any]]

    # Generation output
    answer_index: int
    confidence: float
    reasoning: str
    rule_found: str
    source_reference: Dict[str, Any]

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Graph Nodes
# =============================================================================

# Lazy RAG node initialization to avoid grpcio at module load (macOS mutex.cc issue)
_solver_rag_node = None


def _get_solver_rag_node():
    """Get or create the RAG node (lazy initialization)."""
    global _solver_rag_node
    if _solver_rag_node is None:
        _solver_rag_node = create_rag_node(
            config=RAGConfig(
                max_chars=6000,
                top_k=4,
                include_references=True,
            ),
            query_key="question_text",
        )
    return _solver_rag_node


async def retrieve_rag_node(state: SolverState) -> Dict[str, Any]:
    """
    Retrieve RAG context for the question.

    Uses hybrid retrieval (BM25 + vector) with RRF fusion.
    """
    rag_node = _get_solver_rag_node()
    return await rag_node(state)


@trace_chain(name="generate_answer")
async def generate_answer_node(state: SolverState) -> Dict[str, Any]:
    """
    Generate answer using subject-specific expert prompts.

    Uses RAG context to ground the answer in textbook material.
    """
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    question_text = state.get("question_text", "")
    answers = state.get("answers", [])
    context = state.get("rag_context", "")
    references = state.get("rag_references", [])

    # Get subject-specific prompt template
    prompt_template = SUBJECT_PROMPTS.get(subject, DEFAULT_PROMPT)

    # Build prompt
    prompt = prompt_template.format(
        context=context if context else "Контекст не знайдено.",
        subject=subject,
        grade=grade,
        question=question_text,
        options=_format_options(answers),
    )

    # Generate answer
    result = await generate_json_safe(
        prompt=prompt,
        temperature=0.0,
        default={"answer": 0, "analysis": "Generation failed", "source": 1},
    )

    # Extract fields from result
    answer_index = result.get("answer", result.get("answer_index", 0))
    reasoning = (
        result.get("analysis", "")
        or result.get("solution", "")
        or result.get("reason", "")
        or result.get("reasoning", "")
    )
    rule_found = result.get("rule", result.get("fact", ""))
    source_id = result.get("source", 1)

    # Validate answer_index
    if not isinstance(answer_index, int) or answer_index < 0 or answer_index >= len(answers):
        answer_index = 0

    # Validate source_id
    if not isinstance(source_id, int) or source_id < 1:
        source_id = 1

    # Get source reference details
    source_ref = {}
    if references and 0 < source_id <= len(references):
        source_ref = references[source_id - 1]

    # Build rich reasoning with source
    full_reasoning = reasoning
    if rule_found:
        full_reasoning = f"Правило: {rule_found}. {reasoning}"
    if source_ref:
        full_reasoning += (
            f" [Джерело: {source_ref.get('topic', '')}, "
            f"стор. {source_ref.get('page', '')}]"
        )

    return {
        "answer_index": answer_index,
        "confidence": 0.8,  # Default confidence
        "reasoning": full_reasoning,
        "rule_found": rule_found,
        "source_reference": source_ref,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


# =============================================================================
# Build Graph
# =============================================================================


def build_solver_graph():
    """
    Build the LangGraph workflow for question solving.

    Flow:
        retrieve_rag → generate_answer → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(SolverState)

    # Add nodes
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_answer", generate_answer_node)

    # Add edges
    workflow.set_entry_point("retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow.compile()


# Lazy graph compilation
_solver_graph = None


def get_solver_graph():
    """Get or create the compiled solver graph (lazy initialization)."""
    global _solver_graph
    if _solver_graph is None:
        _solver_graph = build_solver_graph()
    return _solver_graph


# For backwards compatibility - will trigger compilation on first access
class _LazyGraph:
    def __getattr__(self, name):
        return getattr(get_solver_graph(), name)

    def __call__(self, *args, **kwargs):
        return get_solver_graph()(*args, **kwargs)


solver_graph = _LazyGraph()


# =============================================================================
# Public API
# =============================================================================


class SolverResult:
    """Result from solving a single question."""

    def __init__(
        self,
        answer_index: int,
        confidence: float,
        reasoning: str,
        references: List[Dict[str, Any]],
        llm_calls: int = 0,
        model_used: str = "solver-graph",
    ):
        self.answer_index = answer_index
        self.confidence = confidence
        self.reasoning = reasoning
        self.references = references
        self.llm_calls = llm_calls
        self.model_used = model_used

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_index": self.answer_index,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "references": self.references,
            "llm_calls": self.llm_calls,
            "model_used": self.model_used,
        }


async def solve_question(
    question_id: str,
    question_text: str,
    subject: str,
    grade: int,
    answers: List[str],
    correct_indices: Optional[List[int]] = None,
) -> SolverResult:
    """
    Solve a question using the LangGraph workflow.

    Args:
        question_id: Unique question identifier
        question_text: The question text
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        answers: List of answer options
        correct_indices: Optional correct answer indices (for evaluation)

    Returns:
        SolverResult with answer_index, confidence, reasoning, references
    """
    initial_state: SolverState = {
        "question_id": question_id,
        "question_text": question_text,
        "subject": subject,
        "grade": grade,
        "answers": answers,
        "correct_indices": correct_indices or [],
        "rag_context": "",
        "rag_references": [],
        "retrieved_docs": [],
        "matched_topics": [],
        "answer_index": 0,
        "confidence": 0.0,
        "reasoning": "",
        "rule_found": "",
        "source_reference": {},
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_solver_graph()
        final_state = await graph.ainvoke(initial_state)
        return SolverResult(
            answer_index=final_state.get("answer_index", 0),
            confidence=final_state.get("confidence", 0.5),
            reasoning=final_state.get("reasoning", ""),
            references=final_state.get("rag_references", []),
            llm_calls=final_state.get("llm_calls_count", 0),
            model_used="solver-graph",
        )
    except Exception as e:
        logger.error(f"Solver failed: {e}", exc_info=True)
        return SolverResult(
            answer_index=0,
            confidence=0.1,
            reasoning=f"Error: {str(e)}",
            references=[],
            llm_calls=0,
            model_used="solver-graph-error",
        )


async def solve_question_from_dict(question: Dict[str, Any]) -> SolverResult:
    """
    Solve a question from a dict format (backwards compatible with existing API).

    Args:
        question: Dict with keys:
            - question_id
            - question_text
            - global_discipline_name (subject)
            - grade
            - answers
            - correct_answer_indices (optional)

    Returns:
        SolverResult
    """
    return await solve_question(
        question_id=question.get("question_id", ""),
        question_text=question.get("question_text", ""),
        subject=question.get("global_discipline_name", ""),
        grade=question.get("grade", 9),
        answers=question.get("answers", []),
        correct_indices=question.get("correct_answer_indices"),
    )
