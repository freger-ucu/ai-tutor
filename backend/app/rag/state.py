"""
State definition for Agentic RAG pipeline.

Simplified state compared to CRAG - only essential fields.
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass


class AgenticRAGState(TypedDict, total=False):
    """
    Simplified state for Agentic RAG pipeline.

    Only essential fields - no intermediate grading, no multi-query expansion.
    """

    # ===== INPUT =====
    question_id: str
    question_text: str
    subject: str
    grade: int
    answers: List[str]
    correct_indices: List[int]  # For evaluation only

    # ===== RETRIEVAL (Node 1: smart_retrieve) =====
    retrieved_docs: List[Dict[str, Any]]
    retrieval_score: float  # Average RRF score
    topic_match: Optional[Dict[str, Any]]  # Best matching TOC topic
    matched_topics: List[Dict[str, Any]]  # V4: All matched TOC topics (for Ukrainian)

    # ===== AGENT DECISION (Node 2: agent_decision) =====
    agent_decision: str  # "GENERATE" | "RETRY"
    context_quality: float  # 0.0-1.0
    question_type: str  # Subject-specific type
    complexity: str  # "low" | "medium" | "high"
    retry_hint: Optional[str]  # Hint for retry query
    retry_count: int

    # ===== GENERATION (Node 3: unified_generate) =====
    context_text: str  # Formatted context for prompt
    initial_answer: Dict[str, Any]  # First generation result

    # ===== SELF-CONSISTENCY / VOTING =====
    used_self_consistency: bool
    sc_agreement: float  # Agreement score (for voting: agent agreement ratio)

    # ===== OUTPUT =====
    final_answer_index: int
    final_confidence: float
    final_reasoning: str
    references: List[Dict[str, Any]]

    # ===== METADATA =====
    llm_calls_count: int
    error_message: Optional[str]


@dataclass
class SolverResult:
    """Result from solving a single question."""

    answer_index: int
    confidence: float
    reasoning: str
    references: List[Dict[str, Any]]
    llm_calls: int = 0
    model_used: str = "agentic-rag"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_index": self.answer_index,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "references": self.references,
            "llm_calls": self.llm_calls,
            "model_used": self.model_used,
        }


def create_initial_state(question: Dict[str, Any]) -> AgenticRAGState:
    """
    Create initial state from a question dict.

    Args:
        question: Dict with keys:
            - question_id
            - question_text
            - global_discipline_name (subject)
            - grade
            - answers
            - correct_answer_indices (optional)

    Returns:
        Initialized AgenticRAGState
    """
    return AgenticRAGState(
        # Input
        question_id=question.get("question_id", ""),
        question_text=question.get("question_text", ""),
        subject=question.get("global_discipline_name", ""),
        grade=question.get("grade", 9),
        answers=question.get("answers", []),
        correct_indices=question.get("correct_answer_indices", []),

        # Retrieval - will be filled
        retrieved_docs=[],
        retrieval_score=0.0,
        topic_match=None,
        matched_topics=[],

        # Agent decision - will be filled
        agent_decision="GENERATE",
        context_quality=0.0,
        question_type="general",
        complexity="medium",
        retry_hint=None,
        retry_count=0,

        # Generation - will be filled
        context_text="",
        initial_answer={},

        # Self-consistency / Voting
        used_self_consistency=False,
        sc_agreement=0.0,

        # Output - will be filled
        final_answer_index=0,
        final_confidence=0.0,
        final_reasoning="",
        references=[],

        # Metadata
        llm_calls_count=0,
        error_message=None,
    )
