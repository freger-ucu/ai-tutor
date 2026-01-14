"""
Notes Generation Flow (EP3.1 + EP3.2).

Generates lesson notes adapted to student levels with prerequisite-aware recap.

Input (minimal):
    - student_ids: List of student IDs to generate notes for
    - subject: Subject name (Алгебра, Українська мова, Історія України)
    - grade: Grade level (8 or 9)
    - topic_definition: Topic to generate notes about

Flow:
    analyze_students → collect_gaps → retrieve_rag → generate_notes → END

Nodes:
    - analyze_students: Computes level (weak/medium/strong) and aggregated_gaps
    - collect_gaps: Uses LLM to filter gaps to actual prerequisites for the topic
    - retrieve_rag: Retrieves RAG context for topic and prerequisite gaps
    - generate_notes: Generates final notes with recap section if prereqs exist
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

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class NotesState(TypedDict, total=False):
    """State for notes generation flow."""

    # === INPUT (required) ===
    student_ids: List[int]  # Student IDs to generate notes for
    subject: str  # Алгебра, Українська мова, Історія України
    grade: int  # 8 or 9
    topic_definition: str  # Topic to teach

    # === COMPUTED BY analyze_students node ===
    level: str  # "weak" | "medium" | "strong" (computed from student scores)
    aggregated_gaps: Dict[str, Any]  # {weak_topics, skipped_topics, total_students}
    class_id: int  # Detected from student data
    teacher_id: int  # Detected from student data

    # === COMPUTED BY collect_gaps node ===
    student_gaps: List[str]  # All gaps (weak + skipped topics) for potential recap

    # === COMPUTED BY retrieve_rag node ===
    rag_context: str  # Main topic context
    gaps_context: str  # Context for student gaps (for recap)
    rag_references: List[Dict[str, Any]]  # Combined references

    # === OUTPUT (from generate_notes node) ===
    title: str
    contents: str
    teacher_notes: str

    # === METADATA ===
    llm_calls_count: int
    error_message: Optional[str]


# =============================================================================
# Gap Collection & Filtering
# =============================================================================


def get_all_gaps(gaps: Dict[str, Any]) -> List[str]:
    """
    Collect all student gaps (weak_topics + skipped_topics) as a simple list.
    """
    weak_topics = list(gaps.get("weak_topics", {}).keys())
    skipped_topics = list(gaps.get("skipped_topics", {}).keys())

    # Union, remove duplicates, clean whitespace
    all_gaps = []
    seen = set()
    for topic in weak_topics + skipped_topics:
        clean = topic.strip()
        if clean and clean.lower() not in seen:
            all_gaps.append(clean)
            seen.add(clean.lower())

    return all_gaps[:15]  # Limit to 15 candidates


PREREQ_FILTER_PROMPT = """Ти — експерт з навчальних програм української школи.

Тема уроку: {topic}
Предмет: {subject}

Список тем, з якими учні мають проблеми (погані оцінки або пропуски):
{gaps_list}

Твоє завдання: визначити, які з цих тем є ПРЕРЕКВІЗИТАМИ для теми "{topic}".
Пререквізит — це тема, яку НЕОБХІДНО знати, щоб зрозуміти нову тему.

Відповідай ТІЛЬКИ у форматі JSON:
{{"prerequisites": ["тема1", "тема2"]}}

Якщо жодна тема не є пререквізитом — поверни порожній список:
{{"prerequisites": []}}

ВАЖЛИВО: включай ТІЛЬКИ ті теми, які дійсно є пререквізитами. Не вигадуй нових тем."""


# =============================================================================
# Graph Nodes
# =============================================================================


def analyze_students_node(state: NotesState) -> Dict[str, Any]:
    """
    Analyze students to compute level and aggregated gaps.

    This node:
    1. Loads student data from BenchmarkDataLoader
    2. Computes average score across all students
    3. Determines level (weak/medium/strong) based on class quartiles
    4. Aggregates gaps (weak_topics + skipped_topics)
    """
    from app.services.data_loader import get_benchmark_loader
    from app.services.levels import compute_quartiles, assign_level

    student_ids = state.get("student_ids", [])
    subject = state.get("subject", "")

    if not student_ids:
        logger.warning("No student_ids provided, using defaults")
        return {
            "level": "medium",
            "aggregated_gaps": {"weak_topics": {}, "skipped_topics": {}, "total_students": 0},
            "class_id": 0,
            "teacher_id": 0,
        }

    loader = get_benchmark_loader()

    # Get student info to find class_id
    first_student_info = loader.get_student_info(student_ids[0])
    if not first_student_info:
        logger.warning(f"Student {student_ids[0]} not found")
        return {
            "level": "medium",
            "aggregated_gaps": {"weak_topics": {}, "skipped_topics": {}, "total_students": 0},
            "class_id": 0,
            "teacher_id": 0,
        }

    class_id = first_student_info["class_id"]

    # Find teacher_id from scores data
    if loader.scores_df is not None and not loader.scores_df.empty:
        mask = (
            (loader.scores_df["class_id"] == class_id) &
            (loader.scores_df["discipline_name"] == subject) &
            (loader.scores_df["student_id"].isin(student_ids))
        )
        matching = loader.scores_df[mask]
        if not matching.empty:
            teacher_id = int(matching["teacher_id"].iloc[0])
        else:
            teacher_id = 0
    else:
        teacher_id = 0

    # Get all class students to compute quartiles
    all_class_students = loader.get_class_students(class_id, subject, teacher_id)

    if not all_class_students:
        return {
            "level": "medium",
            "aggregated_gaps": {"weak_topics": {}, "skipped_topics": {}, "total_students": len(student_ids)},
            "class_id": class_id,
            "teacher_id": teacher_id,
        }

    # Compute quartiles from all class scores
    all_scores = [s.average_subject_grade for s in all_class_students]
    q1, q3 = compute_quartiles(all_scores)

    # Compute average score for requested students
    requested_students = [s for s in all_class_students if s.student_id in student_ids]
    if requested_students:
        avg_score = sum(s.average_subject_grade for s in requested_students) / len(requested_students)
        level = assign_level(avg_score, q1, q3).value
    else:
        level = "medium"

    # Aggregate gaps for these students
    aggregated_gaps = loader.aggregate_student_gaps(
        student_ids=student_ids,
        class_id=class_id,
        subject=subject,
        teacher_id=teacher_id
    )

    logger.info(f"Analyzed {len(student_ids)} students: level={level}, "
                f"weak_topics={len(aggregated_gaps.get('weak_topics', {}))}, "
                f"skipped_topics={len(aggregated_gaps.get('skipped_topics', {}))}")

    return {
        "level": level,
        "aggregated_gaps": aggregated_gaps,
        "class_id": class_id,
        "teacher_id": teacher_id,
    }


async def collect_gaps_node(state: NotesState) -> Dict[str, Any]:
    """
    Collect student gaps and filter to prerequisites using LLM.

    Steps:
    1. Get all gaps (weak_topics + skipped_topics)
    2. Use LLM to filter which gaps are prerequisites for the topic
    3. Return filtered list as student_gaps
    """
    from app.rag.utils.llm_client import get_llm_client

    gaps = state.get("aggregated_gaps", {})
    topic = state.get("topic_definition", "")
    subject = state.get("subject", "")

    # Get all gaps
    all_gaps = get_all_gaps(gaps)

    if not all_gaps:
        logger.info("No student gaps found")
        return {"student_gaps": [], "llm_calls_count": state.get("llm_calls_count", 0)}

    logger.info(f"Found {len(all_gaps)} student gaps: {all_gaps}")

    # Use LLM to filter prerequisites
    client = get_llm_client()

    gaps_list = "\n".join(f"- {gap}" for gap in all_gaps)
    prompt = PREREQ_FILTER_PROMPT.format(
        topic=topic,
        subject=subject,
        gaps_list=gaps_list,
    )

    try:
        response = await client.generate(
            prompt=prompt,
            temperature=0.0,
            max_tokens=500,
        )

        parsed = parse_json_response(
            response,
            fallback={"prerequisites": []},
            context="prereq_filter",
        )

        prerequisites = parsed.get("prerequisites", [])

        # Trust LLM output - it was given the exact list and asked to select from it
        # Just clean up and deduplicate
        valid_prereqs = [p.strip() for p in prerequisites if p.strip()]

        logger.info(f"LLM filtered to {len(valid_prereqs)} prerequisites: {valid_prereqs}")

        return {
            "student_gaps": valid_prereqs,
            "llm_calls_count": state.get("llm_calls_count", 0) + 1,
        }

    except Exception as e:
        logger.error(f"Failed to filter prerequisites: {e}")
        # On error, return all gaps as fallback
        return {
            "student_gaps": all_gaps,
            "llm_calls_count": state.get("llm_calls_count", 0),
        }


async def retrieve_rag_node(state: NotesState) -> Dict[str, Any]:
    """Retrieve RAG context for topic and student gaps."""
    from app.rag.utils.hybrid_retriever import get_retriever, format_context

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic = state.get("topic_definition", "")
    student_gaps = state.get("student_gaps", [])

    retriever = get_retriever()

    # Retrieve main topic content
    topic_docs = await retriever.retrieve(query=topic, subject=subject, grade=grade, top_k=5)
    topic_context, topic_refs = format_context(topic_docs, max_chars=6000, subject=subject)

    logger.info(f"Retrieved {len(topic_docs)} docs for main topic")

    # Retrieve gap content if there are student gaps
    gaps_context = ""
    gaps_refs = []

    if student_gaps:
        gaps_query = " ".join(student_gaps[:3])  # Top 3 gaps
        gaps_docs = await retriever.retrieve(query=gaps_query, subject=subject, grade=grade, top_k=3)
        gaps_context, gaps_refs = format_context(gaps_docs, max_chars=3000, subject=subject)
        logger.info(f"Retrieved {len(gaps_docs)} docs for student gaps: {student_gaps[:3]}")

    return {
        "rag_context": topic_context,
        "gaps_context": gaps_context,
        "rag_references": topic_refs + gaps_refs,
    }


@trace_chain(name="generate_notes")
async def generate_notes_node(state: NotesState) -> Dict[str, Any]:
    """Generate notes using LLM with RAG context."""
    client = get_llm_client()

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    level = state.get("level", "medium")
    topic_definition = state.get("topic_definition", "")
    rag_context = state.get("rag_context", "")
    gaps_context = state.get("gaps_context", "")
    student_gaps = state.get("student_gaps", [])
    aggregated_gaps = state.get("aggregated_gaps")
    student_ids = state.get("student_ids", [])

    # Build context with clear separation
    if gaps_context and student_gaps:
        combined_context = f"""## МАТЕРІАЛ ДЛЯ ПОВТОРЕННЯ (теми з прогалинами: {', '.join(student_gaps[:5])}):
{gaps_context}

---

## ОСНОВНИЙ МАТЕРІАЛ ТЕМИ:
{rag_context}"""
    else:
        combined_context = rag_context

    # Build prompt
    if len(student_ids) <= 5:
        prompt = build_individual_notes_prompt(
            subject=subject,
            grade=grade,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
            level=level,
            missed_prereqs=student_gaps,  # Pass gaps as potential prereqs
        )
    else:
        prompt = build_level_notes_prompt(
            subject=subject,
            grade=grade,
            level=level,
            topic_definition=topic_definition,
            context=combined_context,
            aggregated_gaps=aggregated_gaps,
            missed_prereqs=student_gaps,  # Pass gaps as potential prereqs
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
        analyze_students → collect_gaps → retrieve_rag → generate_notes → END
    """
    from langgraph.graph import StateGraph, END

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
notes_graph = None


# =============================================================================
# Public API
# =============================================================================


async def generate_notes(
    student_ids: List[int],
    subject: str,
    grade: int,
    topic_definition: str,
) -> Dict[str, Any]:
    """
    Generate notes using the LangGraph workflow.

    Args:
        student_ids: List of student IDs to generate notes for
        subject: Subject name (Алгебра, Українська мова, Історія України)
        grade: Grade level (8 or 9)
        topic_definition: Topic description

    Returns:
        Dict with:
        - title: Lesson title
        - contents: Markdown content with Recap (if prereqs missed) + Lesson
        - teacher_notes: Tips including recap recommendation
        - references: Combined sources (topic + prereqs)
        - level: Computed student level
        - missed_prereqs: List of prerequisite topics that need recap
        - llm_calls: Number of LLM calls made
    """
    initial_state: NotesState = {
        "student_ids": student_ids,
        "subject": subject,
        "grade": grade,
        "topic_definition": topic_definition,
        "level": "",
        "aggregated_gaps": {},
        "class_id": 0,
        "teacher_id": 0,
        "student_gaps": [],
        "rag_context": "",
        "gaps_context": "",
        "rag_references": [],
        "title": "",
        "contents": "",
        "teacher_notes": "",
        "llm_calls_count": 0,
        "error_message": None,
    }

    try:
        graph = get_notes_graph()
        final_state = await graph.ainvoke(initial_state)
        return {
            "title": final_state.get("title", topic_definition),
            "contents": final_state.get("contents", ""),
            "teacher_notes": final_state.get("teacher_notes", ""),
            "references": final_state.get("rag_references", []),
            "level": final_state.get("level", "medium"),
            "student_gaps": final_state.get("student_gaps", []),
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