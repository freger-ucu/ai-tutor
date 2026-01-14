"""
Notes Generation Flow (EP3.1 + EP3.2).

Generates lesson notes adapted to student levels with prerequisite detection.

Flow:
    aggregate_gaps → detect_prereqs → retrieve_rag (parallel) → generate_notes → format_response

Features:
- Detects prerequisites from student weak/skipped topics
- RAG retrieves both: topic content + prerequisite content
- Generated notes include recap section for prerequisites
- Teacher notes advise which topics need review
"""

import logging
from typing import TypedDict, List, Dict, Any, Optional

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.utils.json_parser import parse_json_response
from app.prompts.notes_generator import (
    build_level_notes_prompt,
    build_individual_notes_prompt,
    NOTES_SYSTEM_PROMPT,
)
from ..shared.rag_node import create_rag_node, RAGConfig

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class NotesState(TypedDict, total=False):
    """State for notes generation flow."""

    # Input
    subject: str
    grade: int
    topic_definition: str
    level: str  # "weak" | "medium" | "strong"
    student_ids: Optional[List[str]]
    aggregated_gaps: Optional[Dict[str, Any]]

    # Prerequisite detection
    prereq_queries: List[str]  # Topics to retrieve for recap
    prereq_topics: List[str]  # Detected prerequisite topics

    # RAG output
    rag_context: str  # Main topic context
    prereq_context: str  # Prerequisites context
    rag_references: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]

    # Generation output
    title: str
    contents: str
    teacher_notes: str
    recap_section: str  # Generated recap for prerequisites

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Prerequisite Detection
# =============================================================================

# Static mapping of topics to their prerequisites
# This can be expanded or replaced with LLM-based detection later
PREREQ_MAP: Dict[str, List[str]] = {
    # Algebra topics
    "квадратні рівняння": ["дискримінант", "формули коренів", "квадратний тричлен"],
    "система рівнянь": ["лінійні рівняння", "метод підстановки"],
    "нерівності": ["властивості нерівностей", "числова пряма"],
    "функції": ["графіки", "область визначення", "множина значень"],
    "геометрична прогресія": ["арифметична прогресія", "послідовності"],
    # Ukrainian language topics
    "дієприкметники": ["дієслово", "прикметник", "дієприкметниковий зворот"],
    "дієприслівники": ["дієслово", "прислівник", "дієприслівниковий зворот"],
    "складне речення": ["просте речення", "сполучники сурядності", "сполучники підрядності"],
    "пунктуація": ["розділові знаки", "кома", "тире"],
    # History topics
    "друга світова війна": ["міжвоєнний період", "передумови війни"],
    "незалежність україни": ["перебудова", "розпад срср"],
}


def detect_prerequisites(
    gaps: Dict[str, Any],
    topic: str,
    subject: str,
) -> List[str]:
    """
    Map student gaps to prerequisite topics that need recap.

    Args:
        gaps: Aggregated gaps with weak_topics and skipped_topics
        topic: Current topic being studied
        subject: Subject name

    Returns:
        List of prerequisite topic names for RAG retrieval
    """
    prereqs = set()

    # Get weak topics from gaps
    weak_topics = gaps.get("weak_topics", {})
    for weak_topic in weak_topics.keys():
        # Clean topic name
        clean_topic = weak_topic.strip().lower()
        # Look up prerequisites
        for key, prereq_list in PREREQ_MAP.items():
            if key in clean_topic or clean_topic in key:
                prereqs.update(prereq_list)

    # Add skipped topics directly (they need introduction)
    skipped_topics = gaps.get("skipped_topics", {})
    for skipped in skipped_topics.keys():
        prereqs.add(skipped.strip())

    # Check if current topic has known prerequisites
    topic_lower = topic.lower()
    for key, prereq_list in PREREQ_MAP.items():
        if key in topic_lower:
            prereqs.update(prereq_list)

    return list(prereqs)[:5]  # Limit to 5 prereqs


# =============================================================================
# Graph Nodes
# =============================================================================


async def aggregate_gaps_node(state: NotesState) -> Dict[str, Any]:
    """
    Aggregate student gaps from input or fetch from student data.

    This node prepares the aggregated_gaps if not already provided.
    """
    logger.info(f"Aggregating gaps for topic: {state.get('topic_definition', '')}")

    # If gaps already provided, pass through
    if state.get("aggregated_gaps"):
        return {}

    # Otherwise return empty gaps (no preprocessing needed)
    return {"aggregated_gaps": {"weak_topics": {}, "skipped_topics": {}, "total_students": 0}}


def detect_prereqs_node(state: NotesState) -> Dict[str, Any]:
    """
    Detect prerequisite topics from student gaps.

    Maps gaps to prerequisite topics that need recap in notes.
    """
    gaps = state.get("aggregated_gaps", {})
    topic = state.get("topic_definition", "")
    subject = state.get("subject", "")

    prereq_topics = detect_prerequisites(gaps, topic, subject)

    # Create queries for RAG retrieval
    prereq_queries = []
    for prereq in prereq_topics:
        prereq_queries.append(f"{prereq} пояснення основи")

    logger.info(f"Detected {len(prereq_topics)} prerequisites: {prereq_topics}")

    return {
        "prereq_topics": prereq_topics,
        "prereq_queries": prereq_queries,
    }


# Create configurable RAG node for notes
_notes_rag_node = create_rag_node(
    config=RAGConfig(
        max_chars=8000,
        top_k=5,
        parallel_queries=True,
        include_references=True,
    ),
    query_key="topic_definition",
)


async def retrieve_rag_node(state: NotesState) -> Dict[str, Any]:
    """
    Retrieve RAG context for topic and prerequisites.

    Performs parallel retrieval if prerequisites detected.
    """
    return await _notes_rag_node(state)


@trace_chain(name="generate_notes")
async def generate_notes_node(state: NotesState) -> Dict[str, Any]:
    """
    Generate notes using LLM with RAG context.

    Combines main topic context and prerequisite context into a single generation.
    """
    client = get_llm_client()

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    level = state.get("level", "medium")
    topic_definition = state.get("topic_definition", "")
    rag_context = state.get("rag_context", "")
    prereq_context = state.get("prereq_context", "")
    aggregated_gaps = state.get("aggregated_gaps")

    # Combine contexts for prompt
    combined_context = rag_context
    if prereq_context:
        combined_context = f"""## МАТЕРІАЛ ДЛЯ ПОВТОРЕННЯ (пререквізити):
{prereq_context}

---

## ОСНОВНИЙ МАТЕРІАЛ:
{rag_context}"""

    # Build prompt based on whether we have student-specific info
    if state.get("student_ids"):
        prompt = build_individual_notes_prompt(
            subject=subject,
            grade=grade,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
            level=level,
        )
    else:
        prompt = build_level_notes_prompt(
            subject=subject,
            grade=grade,
            level=level,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
        )

    # Generate notes
    response = await client.generate(
        prompt=f"{NOTES_SYSTEM_PROMPT}\n\n{prompt}",
        temperature=0.0,
        max_tokens=4000,
    )

    # Parse response
    parsed = parse_json_response(
        response,
        fallback={"title": topic_definition, "contents": "", "teacher_notes": ""},
    )

    # Build recap section if prerequisites exist
    recap_section = ""
    prereq_topics = state.get("prereq_topics", [])
    if prereq_topics and prereq_context:
        recap_section = f"""## 📚 Повторення (Recap)
Перед вивченням нової теми, повторимо важливі поняття:

{prereq_context[:2000]}

---
"""

    return {
        "title": parsed.get("title", topic_definition),
        "contents": parsed.get("contents", ""),
        "teacher_notes": parsed.get("teacher_notes", ""),
        "recap_section": recap_section,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


def format_response_node(state: NotesState) -> Dict[str, Any]:
    """
    Format final notes response.

    Combines recap section with main content for final output.
    """
    contents = state.get("contents", "")
    recap = state.get("recap_section", "")

    # Prepend recap to contents if exists
    if recap:
        final_contents = f"{recap}\n{contents}"
    else:
        final_contents = contents

    return {"contents": final_contents}


# =============================================================================
# Build Graph
# =============================================================================


def build_notes_graph():
    """
    Build the LangGraph workflow for notes generation.

    Flow:
        aggregate_gaps → detect_prereqs → retrieve_rag → generate_notes → format_response → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(NotesState)

    # Add nodes
    workflow.add_node("aggregate_gaps", aggregate_gaps_node)
    workflow.add_node("detect_prereqs", detect_prereqs_node)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_notes", generate_notes_node)
    workflow.add_node("format_response", format_response_node)

    # Add edges
    workflow.set_entry_point("aggregate_gaps")
    workflow.add_edge("aggregate_gaps", "detect_prereqs")
    workflow.add_edge("detect_prereqs", "retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_notes")
    workflow.add_edge("generate_notes", "format_response")
    workflow.add_edge("format_response", END)

    return workflow.compile()


# Lazy graph compilation
_notes_graph = None


def get_notes_graph():
    """Get or create the compiled notes graph (lazy initialization)."""
    global _notes_graph
    if _notes_graph is None:
        _notes_graph = build_notes_graph()
    return _notes_graph


# For backwards compatibility
notes_graph = None  # Will be set on first use


# =============================================================================
# Public API
# =============================================================================


async def generate_notes(
    subject: str,
    grade: int,
    topic_definition: str,
    level: str = "medium",
    student_ids: Optional[List[str]] = None,
    aggregated_gaps: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate notes using the LangGraph workflow.

    Args:
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        level: Student level (weak/medium/strong)
        student_ids: Optional list of student IDs for personalization
        aggregated_gaps: Optional pre-aggregated gaps data

    Returns:
        Dict with title, contents, teacher_notes, and metadata
    """
    initial_state: NotesState = {
        "subject": subject,
        "grade": grade,
        "topic_definition": topic_definition,
        "level": level,
        "student_ids": student_ids,
        "aggregated_gaps": aggregated_gaps,
        "prereq_queries": [],
        "prereq_topics": [],
        "rag_context": "",
        "prereq_context": "",
        "rag_references": [],
        "retrieved_docs": [],
        "title": "",
        "contents": "",
        "teacher_notes": "",
        "recap_section": "",
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_notes_graph()
        final_state = await graph.ainvoke(initial_state)
        return {
            "title": final_state.get("title", topic_definition),
            "contents": final_state.get("contents", ""),
            "teacher_notes": final_state.get("teacher_notes", ""),
            "references": final_state.get("rag_references", []),
            "prereq_topics": final_state.get("prereq_topics", []),
            "llm_calls": final_state.get("llm_calls_count", 0),
        }
    except Exception as e:
        logger.error(f"Notes generation failed: {e}", exc_info=True)
        return {
            "title": topic_definition,
            "contents": "",
            "teacher_notes": "",
            "error": str(e),
        }
