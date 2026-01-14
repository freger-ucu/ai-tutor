"""
Notes Generation Flow (EP3.1 + EP3.2).

Generates lesson notes adapted to student levels with prerequisite-aware recap.

Flow:
    aggregate_gaps → filter_missed_prereqs → retrieve_rag (topic + prereqs) → generate_notes → END

Logic:
1. Aggregate gaps: collect weak_topics and skipped_topics from student data
2. Filter prereqs: find which gaps are prerequisites of the CURRENT topic
   - Only include prereqs that students actually missed/struggled with
   - Don't include all prereqs - just the ones that overlap with gaps
3. RAG retrieve: get content for main topic + missed prerequisites
4. Generate notes with structure:
   - ## Повторення (Recap) - if there are missed prereqs
   - ## Урок (Lesson) - main topic content
5. Teacher notes mention to do recap first if applicable
6. Sources include both topic and recap references
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

    # Prerequisite filtering (gaps ∩ topic prereqs)
    missed_prereqs: List[str]  # Prerequisites that students actually missed/struggled with

    # RAG output
    rag_context: str  # Main topic context
    prereq_context: str  # Prerequisites context (for missed prereqs only)
    rag_references: List[Dict[str, Any]]  # Combined: topic + prereq references
    topic_references: List[Dict[str, Any]]  # Topic-only references
    prereq_references: List[Dict[str, Any]]  # Prereq-only references

    # Generation output
    title: str
    contents: str
    teacher_notes: str

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
    "квадратні рівняння": ["дискримінант", "формули коренів", "квадратний тричлен", "лінійні рівняння"],
    "системи рівнянь": ["лінійні рівняння", "метод підстановки", "метод додавання"],
    "нерівності": ["властивості нерівностей", "числова пряма", "лінійні рівняння"],
    "квадратні нерівності": ["квадратні рівняння", "дискримінант", "парабола"],
    "функції": ["графіки", "область визначення", "множина значень", "координатна площина"],
    "квадратична функція": ["квадратні рівняння", "парабола", "вершина параболи"],
    "геометрична прогресія": ["арифметична прогресія", "послідовності"],
    "арифметична прогресія": ["послідовності", "формули"],
    # Ukrainian language topics
    "дієприкметники": ["дієслово", "прикметник", "дієприкметниковий зворот"],
    "дієприслівники": ["дієслово", "прислівник", "дієприслівниковий зворот"],
    "складне речення": ["просте речення", "сполучники сурядності", "сполучники підрядності"],
    "складнопідрядне речення": ["складне речення", "сполучники підрядності", "підрядні частини"],
    "пунктуація": ["розділові знаки", "кома", "тире", "двокрапка"],
    # History topics
    "друга світова війна": ["міжвоєнний період", "передумови війни", "версальський договір"],
    "незалежність україни": ["перебудова", "розпад срср", "референдум 1991"],
    "українська революція": ["перша світова війна", "російська революція"],
}


def get_topic_prerequisites(topic: str) -> List[str]:
    """
    Get known prerequisites for a topic.

    Args:
        topic: Topic name to look up

    Returns:
        List of prerequisite topic names
    """
    topic_lower = topic.lower().strip()

    # Direct match
    for key, prereqs in PREREQ_MAP.items():
        if key in topic_lower or topic_lower in key:
            return prereqs

    # Partial match - check if any key words match
    for key, prereqs in PREREQ_MAP.items():
        key_words = set(key.split())
        topic_words = set(topic_lower.split())
        if key_words & topic_words:  # Intersection
            return prereqs

    return []


def filter_missed_prerequisites(
    gaps: Dict[str, Any],
    topic: str,
) -> List[str]:
    """
    Find prerequisites of the current topic that students actually missed or struggled with.

    This is the intersection of:
    - Prerequisites of the current topic (from PREREQ_MAP)
    - Student gaps (weak_topics + skipped_topics)

    Args:
        gaps: Aggregated gaps with weak_topics and skipped_topics
        topic: Current topic being studied

    Returns:
        List of prerequisite topics that need recap (gaps ∩ prereqs)
    """
    # Get all known prerequisites for this topic
    topic_prereqs = set(p.lower() for p in get_topic_prerequisites(topic))

    if not topic_prereqs:
        logger.info(f"No known prerequisites for topic: {topic}")
        return []

    # Collect all student gaps (weak + skipped)
    weak_topics = set(t.strip().lower() for t in gaps.get("weak_topics", {}).keys())
    skipped_topics = set(t.strip().lower() for t in gaps.get("skipped_topics", {}).keys())
    all_gaps = weak_topics | skipped_topics

    if not all_gaps:
        logger.info("No student gaps found")
        return []

    # Find intersection: prereqs that students actually missed
    missed_prereqs = []
    for gap in all_gaps:
        for prereq in topic_prereqs:
            # Fuzzy match - check if gap contains prereq or vice versa
            if prereq in gap or gap in prereq:
                # Use the original gap name (preserves case)
                original_name = next(
                    (t for t in list(gaps.get("weak_topics", {}).keys()) +
                     list(gaps.get("skipped_topics", {}).keys())
                     if t.strip().lower() == gap),
                    prereq
                )
                if original_name not in missed_prereqs:
                    missed_prereqs.append(original_name)
                break

    logger.info(f"Topic '{topic}' prereqs: {topic_prereqs}")
    logger.info(f"Student gaps: {all_gaps}")
    logger.info(f"Missed prereqs (intersection): {missed_prereqs}")

    return missed_prereqs[:5]  # Limit to 5


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


def filter_prereqs_node(state: NotesState) -> Dict[str, Any]:
    """
    Filter prerequisites: find which student gaps are actually prereqs of the current topic.

    Only includes prereqs that students missed/struggled with (intersection logic).
    """
    gaps = state.get("aggregated_gaps", {})
    topic = state.get("topic_definition", "")

    missed_prereqs = filter_missed_prerequisites(gaps, topic)

    logger.info(f"Filtered to {len(missed_prereqs)} missed prerequisites: {missed_prereqs}")

    return {"missed_prereqs": missed_prereqs}


# Create configurable RAG node for main topic
_topic_rag_node = create_rag_node(
    config=RAGConfig(
        max_chars=6000,
        top_k=5,
        parallel_queries=False,
        include_references=True,
    ),
    query_key="topic_definition",
)

# Create configurable RAG node for prerequisites
_prereq_rag_node = create_rag_node(
    config=RAGConfig(
        max_chars=3000,
        top_k=3,
        parallel_queries=False,
        include_references=True,
    ),
    query_key="prereq_query",
)


async def retrieve_rag_node(state: NotesState) -> Dict[str, Any]:
    """
    Retrieve RAG context for topic and missed prerequisites.

    1. Always retrieves main topic content
    2. If there are missed prereqs, retrieves their content too
    3. Combines all references (topic + prereqs)
    """
    from app.rag.utils.hybrid_retriever import get_retriever, format_context

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic = state.get("topic_definition", "")
    missed_prereqs = state.get("missed_prereqs", [])

    retriever = get_retriever()

    # 1. Retrieve main topic content
    topic_docs = await retriever.retrieve(
        query=topic,
        subject=subject,
        grade=grade,
        top_k=5
    )
    topic_context, topic_refs = format_context(topic_docs, max_chars=6000, subject=subject)

    logger.info(f"Retrieved {len(topic_docs)} docs for main topic")

    # 2. Retrieve prerequisite content if there are missed prereqs
    prereq_context = ""
    prereq_refs = []

    if missed_prereqs:
        # Combine missed prereqs into a single query
        prereq_query = " ".join(missed_prereqs[:3])  # Top 3 missed prereqs
        prereq_docs = await retriever.retrieve(
            query=prereq_query,
            subject=subject,
            grade=grade,
            top_k=3
        )
        prereq_context, prereq_refs = format_context(prereq_docs, max_chars=3000, subject=subject)

        logger.info(f"Retrieved {len(prereq_docs)} docs for prerequisites: {missed_prereqs}")

    # 3. Combine references (topic + prereqs)
    all_refs = topic_refs + prereq_refs

    return {
        "rag_context": topic_context,
        "prereq_context": prereq_context,
        "topic_references": topic_refs,
        "prereq_references": prereq_refs,
        "rag_references": all_refs,
    }


@trace_chain(name="generate_notes")
async def generate_notes_node(state: NotesState) -> Dict[str, Any]:
    """
    Generate notes using LLM with RAG context.

    Structure:
    - If missed prereqs exist: ## Повторення (Recap) + ## Урок (Lesson)
    - If no missed prereqs: ## Урок (Lesson) only

    Teacher notes will mention to do recap first if applicable.
    """
    client = get_llm_client()

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    level = state.get("level", "medium")
    topic_definition = state.get("topic_definition", "")
    rag_context = state.get("rag_context", "")
    prereq_context = state.get("prereq_context", "")
    missed_prereqs = state.get("missed_prereqs", [])
    aggregated_gaps = state.get("aggregated_gaps")

    # Build context with clear separation
    if prereq_context and missed_prereqs:
        combined_context = f"""## МАТЕРІАЛ ДЛЯ ПОВТОРЕННЯ (пререквізити: {', '.join(missed_prereqs)}):
{prereq_context}

---

## ОСНОВНИЙ МАТЕРІАЛ ТЕМИ:
{rag_context}"""
    else:
        combined_context = rag_context

    # Build prompt based on whether we have student-specific info
    if state.get("student_ids"):
        prompt = build_individual_notes_prompt(
            subject=subject,
            grade=grade,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
            level=level,
            missed_prereqs=missed_prereqs,
        )
    else:
        prompt = build_level_notes_prompt(
            subject=subject,
            grade=grade,
            level=level,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
            missed_prereqs=missed_prereqs,
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

    return {
        "title": parsed.get("title", topic_definition),
        "contents": parsed.get("contents", ""),
        "teacher_notes": parsed.get("teacher_notes", ""),
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


# =============================================================================
# Build Graph
# =============================================================================


def build_notes_graph():
    """
    Build the LangGraph workflow for notes generation.

    Flow:
        aggregate_gaps → filter_prereqs → retrieve_rag → generate_notes → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(NotesState)

    # Add nodes
    workflow.add_node("aggregate_gaps", aggregate_gaps_node)
    workflow.add_node("filter_prereqs", filter_prereqs_node)
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("generate_notes", generate_notes_node)

    # Add edges
    workflow.set_entry_point("aggregate_gaps")
    workflow.add_edge("aggregate_gaps", "filter_prereqs")
    workflow.add_edge("filter_prereqs", "retrieve_rag")
    workflow.add_edge("retrieve_rag", "generate_notes")
    workflow.add_edge("generate_notes", END)

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
        Dict with:
        - title: Lesson title
        - contents: Markdown content with Recap (if prereqs missed) + Lesson
        - teacher_notes: Tips including recap recommendation
        - references: Combined sources (topic + prereqs)
        - missed_prereqs: List of prerequisite topics that need recap
        - llm_calls: Number of LLM calls made
    """
    initial_state: NotesState = {
        "subject": subject,
        "grade": grade,
        "topic_definition": topic_definition,
        "level": level,
        "student_ids": student_ids,
        "aggregated_gaps": aggregated_gaps,
        "missed_prereqs": [],
        "rag_context": "",
        "prereq_context": "",
        "rag_references": [],
        "topic_references": [],
        "prereq_references": [],
        "title": "",
        "contents": "",
        "teacher_notes": "",
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
            "missed_prereqs": final_state.get("missed_prereqs", []),
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
