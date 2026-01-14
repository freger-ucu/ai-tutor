"""
Test Generation Flow (EP4).

Generates a pool of validated test questions using batch generation.

Flow:
    retrieve_context → generate_batches (parallel) → validate_samples → retry_failed → finalize

Key Design:
- 3 batch calls (easy/medium/hard), each generating 10 questions
- CPU validation on all questions (format, fields, uniqueness)
- Sample validation: 3 random MC questions per batch via solver
- If >1 of 3 fail → regenerate entire batch
- Max 2 retries per batch

LLM Call Estimate:
- 3 generation calls (easy/medium/hard batches)
- 9 solver calls for validation (3 per batch, in parallel)
- Total: ~12 LLM calls (vs 60+ in old design)
"""

import asyncio
import logging
import random
from typing import TypedDict, List, Dict, Any, Optional, Literal

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.utils.json_parser import parse_json_response
from app.prompts.test_generator import (
    build_chunked_test_prompt,
    TEST_GENERATOR_SYSTEM_PROMPT,
)
from ..shared.rag_node import create_rag_node, RAGConfig
from ..shared.cpu_validators import validate_batch_questions, ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# State Definition
# =============================================================================


class BatchState(TypedDict):
    """State for a single difficulty batch."""

    difficulty: str
    questions: List[Dict[str, Any]]
    is_valid: bool
    attempts: int
    validation_failures: List[str]


class TestGenState(TypedDict, total=False):
    """State for test generation flow."""

    # Input
    subject: str
    grade: int
    topic_definition: str
    num_questions: int  # Target total (default 30)
    max_retries: int  # Max retries per batch (default 2)

    # RAG output
    rag_context: str
    rag_references: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]

    # Batch states
    easy_batch: BatchState
    medium_batch: BatchState
    hard_batch: BatchState

    # Final output
    questions: List[Dict[str, Any]]  # All valid questions
    existing_question_texts: List[str]  # For deduplication

    # Statistics
    total_generation_calls: int
    total_validation_calls: int
    retries_used: int
    batches_regenerated: int

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Constants
# =============================================================================

QUESTIONS_PER_BATCH = 10
SAMPLE_SIZE = 3  # Questions to validate per batch
PASS_THRESHOLD = 2  # At least 2 of 3 must pass


# =============================================================================
# Graph Nodes
# =============================================================================

# Lazy RAG node initialization to avoid grpcio at module load (macOS mutex.cc issue)
_test_gen_rag_node = None


def _get_test_gen_rag_node():
    """Get or create the RAG node (lazy initialization)."""
    global _test_gen_rag_node
    if _test_gen_rag_node is None:
        _test_gen_rag_node = create_rag_node(
            config=RAGConfig(
                max_chars=6000,
                top_k=4,
                include_references=False,
            ),
            query_key="topic_definition",
        )
    return _test_gen_rag_node


async def retrieve_context_node(state: TestGenState) -> Dict[str, Any]:
    """Retrieve RAG context for the topic."""
    logger.info(f"Retrieving context for topic: {state.get('topic_definition', '')}")
    rag_node = _get_test_gen_rag_node()
    return await rag_node(state)


def init_batches_node(state: TestGenState) -> Dict[str, Any]:
    """Initialize batch states for each difficulty level."""
    return {
        "easy_batch": {
            "difficulty": "easy",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "medium_batch": {
            "difficulty": "medium",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "hard_batch": {
            "difficulty": "hard",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "questions": [],
        "existing_question_texts": [],
        "total_generation_calls": 0,
        "total_validation_calls": 0,
        "retries_used": 0,
        "batches_regenerated": 0,
    }


@trace_chain(name="generate_batch")
async def _generate_single_batch(
    subject: str,
    grade: int,
    topic_definition: str,
    context: str,
    difficulty: str,
    existing_texts: List[str],
) -> tuple[List[Dict[str, Any]], List[str]]:
    """
    Generate a batch of questions for one difficulty level.

    Returns:
        Tuple of (valid_questions, validation_errors)
    """
    client = get_llm_client()

    prompt = build_chunked_test_prompt(
        subject=subject,
        grade=grade,
        topic_definition=topic_definition,
        context=context,
        difficulty=difficulty,
        num_questions=QUESTIONS_PER_BATCH,
    )

    response = await client.generate(
        prompt=f"{TEST_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}",
        temperature=0.7,
        max_tokens=4000,
    )

    # Parse response
    parsed = parse_json_response(
        response,
        fallback={"questions": []},
        context=f"TestGen-{difficulty}",
    )

    raw_questions = parsed.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []

    # Normalize question format
    normalized = []
    for q in raw_questions:
        if not isinstance(q, dict):
            continue

        # Ensure required fields
        q["difficulty"] = difficulty
        if "type" not in q:
            q["type"] = "multiple_choice" if "options" in q else "open"

        # Convert correct_answer letter to index for MC questions
        if q.get("type") == "multiple_choice" and "correct_answer" in q:
            answer_letter = str(q["correct_answer"]).strip().upper()
            letter_to_index = {"A": 0, "B": 1, "C": 2, "D": 3}
            q["correct_answer_index"] = letter_to_index.get(answer_letter, 0)

        normalized.append(q)

    # CPU validation
    existing_set = set(existing_texts)
    valid_questions, failures = validate_batch_questions(normalized, existing_set)

    validation_errors = [
        f"Q{i}: {', '.join(r.issues)}" for i, r in failures
    ]

    return valid_questions, validation_errors


async def generate_batches_node(state: TestGenState) -> Dict[str, Any]:
    """
    Generate all three difficulty batches in parallel.
    """
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic_definition = state.get("topic_definition", "")
    context = state.get("rag_context", "")
    existing_texts = state.get("existing_question_texts", [])

    # Get current batch states
    easy_batch = state.get("easy_batch", {})
    medium_batch = state.get("medium_batch", {})
    hard_batch = state.get("hard_batch", {})

    # Only generate for batches that need it
    batches_to_generate = []
    if not easy_batch.get("is_valid", False):
        batches_to_generate.append(("easy", easy_batch))
    if not medium_batch.get("is_valid", False):
        batches_to_generate.append(("medium", medium_batch))
    if not hard_batch.get("is_valid", False):
        batches_to_generate.append(("hard", hard_batch))

    if not batches_to_generate:
        return {}

    # Generate batches in parallel
    tasks = []
    for difficulty, batch in batches_to_generate:
        task = _generate_single_batch(
            subject=subject,
            grade=grade,
            topic_definition=topic_definition,
            context=context,
            difficulty=difficulty,
            existing_texts=existing_texts,
        )
        tasks.append((difficulty, task))

    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    # Update batch states
    updates = {
        "total_generation_calls": state.get("total_generation_calls", 0) + len(batches_to_generate),
        "llm_calls_count": state.get("llm_calls_count", 0) + len(batches_to_generate),
    }

    for i, (difficulty, _) in enumerate(tasks):
        result = results[i]
        if isinstance(result, Exception):
            logger.error(f"Batch generation failed for {difficulty}: {result}")
            batch_update = {
                "difficulty": difficulty,
                "questions": [],
                "is_valid": False,
                "attempts": state.get(f"{difficulty}_batch", {}).get("attempts", 0) + 1,
                "validation_failures": [str(result)],
            }
        else:
            questions, errors = result
            batch_update = {
                "difficulty": difficulty,
                "questions": questions,
                "is_valid": False,  # Will be set after sample validation
                "attempts": state.get(f"{difficulty}_batch", {}).get("attempts", 0) + 1,
                "validation_failures": errors,
            }

        updates[f"{difficulty}_batch"] = batch_update

    return updates


@trace_chain(name="validate_samples")
async def _validate_sample_questions(
    questions: List[Dict[str, Any]],
    subject: str,
    grade: int,
    sample_size: int = SAMPLE_SIZE,
) -> tuple[int, int, List[str]]:
    """
    Validate a sample of MC questions using the solver.

    Returns:
        Tuple of (passed_count, total_validated, failure_reasons)
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from .solver import solve_question

    # Filter MC questions only
    mc_questions = [q for q in questions if q.get("type") == "multiple_choice"]

    if not mc_questions:
        # No MC questions to validate, assume pass
        return sample_size, sample_size, []

    # Select random sample
    sample = random.sample(mc_questions, min(sample_size, len(mc_questions)))

    # Validate each in parallel
    tasks = []
    for q in sample:
        task = solve_question(
            question_id=f"validation-{random.randint(1000, 9999)}",
            question_text=q.get("question", ""),
            subject=subject,
            grade=grade,
            answers=q.get("options", []),
            correct_indices=[q.get("correct_answer_index", 0)],
        )
        tasks.append((q, task))

    results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

    # Check results
    passed = 0
    failures = []

    for i, (q, _) in enumerate(tasks):
        result = results[i]
        if isinstance(result, Exception):
            failures.append(f"Solver error: {result}")
            continue

        expected_index = q.get("correct_answer_index", 0)
        solver_index = result.answer_index
        confidence = result.confidence

        # Pass criteria:
        # 1. Solver finds the same answer
        # 2. Confidence is high (>0.7)
        if solver_index == expected_index and confidence >= 0.7:
            passed += 1
        else:
            failures.append(
                f"Q: {q.get('question', '')[:50]}... "
                f"Expected: {expected_index}, Got: {solver_index}, Conf: {confidence:.2f}"
            )

    return passed, len(sample), failures


async def validate_samples_node(state: TestGenState) -> Dict[str, Any]:
    """
    Validate samples from each batch using the solver.

    For each batch, validate 3 random MC questions.
    If >= 2 pass, mark batch as valid.
    """
    subject = state.get("subject", "")
    grade = state.get("grade", 9)

    updates = {
        "total_validation_calls": state.get("total_validation_calls", 0),
        "llm_calls_count": state.get("llm_calls_count", 0),
    }

    for difficulty in ["easy", "medium", "hard"]:
        batch = state.get(f"{difficulty}_batch", {})

        # Skip already valid batches
        if batch.get("is_valid", False):
            continue

        questions = batch.get("questions", [])
        if not questions:
            continue

        # Validate sample
        passed, total, failures = await _validate_sample_questions(
            questions=questions,
            subject=subject,
            grade=grade,
        )

        updates["total_validation_calls"] += total
        updates["llm_calls_count"] += total

        # Check if batch passes
        if passed >= PASS_THRESHOLD:
            batch_update = dict(batch)
            batch_update["is_valid"] = True
            batch_update["validation_failures"] = []
            logger.info(f"✓ {difficulty} batch passed validation ({passed}/{total})")
        else:
            batch_update = dict(batch)
            batch_update["is_valid"] = False
            batch_update["validation_failures"] = failures
            logger.info(f"✗ {difficulty} batch failed validation ({passed}/{total}): {failures}")

        updates[f"{difficulty}_batch"] = batch_update

    return updates


def check_retry_needed(state: TestGenState) -> Literal["retry", "finalize"]:
    """Check if any batches need retry."""
    max_retries = state.get("max_retries", 2)

    for difficulty in ["easy", "medium", "hard"]:
        batch = state.get(f"{difficulty}_batch", {})
        if not batch.get("is_valid", False) and batch.get("attempts", 0) < max_retries:
            return "retry"

    return "finalize"


def prepare_retry_node(state: TestGenState) -> Dict[str, Any]:
    """Prepare state for retry of failed batches."""
    updates = {
        "retries_used": state.get("retries_used", 0) + 1,
        "batches_regenerated": state.get("batches_regenerated", 0),
    }

    # Count batches that will be regenerated
    for difficulty in ["easy", "medium", "hard"]:
        batch = state.get(f"{difficulty}_batch", {})
        if not batch.get("is_valid", False):
            updates["batches_regenerated"] += 1

    return updates


def finalize_node(state: TestGenState) -> Dict[str, Any]:
    """
    Collect all valid questions from batches.
    """
    all_questions = []
    existing_texts = set()

    for difficulty in ["easy", "medium", "hard"]:
        batch = state.get(f"{difficulty}_batch", {})
        if batch.get("is_valid", False):
            for q in batch.get("questions", []):
                q_text = q.get("question", "")
                if q_text and q_text not in existing_texts:
                    all_questions.append(q)
                    existing_texts.add(q_text)

    logger.info(f"Finalized test generation with {len(all_questions)} questions")
    logger.info(f"Stats: generation_calls={state.get('total_generation_calls', 0)}, "
                f"validation_calls={state.get('total_validation_calls', 0)}, "
                f"retries={state.get('retries_used', 0)}")

    return {
        "questions": all_questions,
        "existing_question_texts": list(existing_texts),
    }


# =============================================================================
# Build Graph
# =============================================================================


def build_test_gen_graph():
    """
    Build the LangGraph workflow for test generation.

    Flow:
        retrieve_context → init_batches → generate_batches → validate_samples
        → (retry if needed) → finalize → END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(TestGenState)

    # Add nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("init_batches", init_batches_node)
    workflow.add_node("generate_batches", generate_batches_node)
    workflow.add_node("validate_samples", validate_samples_node)
    workflow.add_node("prepare_retry", prepare_retry_node)
    workflow.add_node("finalize", finalize_node)

    # Add edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "init_batches")
    workflow.add_edge("init_batches", "generate_batches")
    workflow.add_edge("generate_batches", "validate_samples")

    # Conditional: retry or finalize
    workflow.add_conditional_edges(
        "validate_samples",
        check_retry_needed,
        {
            "retry": "prepare_retry",
            "finalize": "finalize",
        },
    )
    workflow.add_edge("prepare_retry", "generate_batches")
    workflow.add_edge("finalize", END)

    return workflow.compile()


# Lazy graph compilation
_test_gen_graph = None


def get_test_gen_graph():
    """Get or create the compiled test gen graph (lazy initialization)."""
    global _test_gen_graph
    if _test_gen_graph is None:
        _test_gen_graph = build_test_gen_graph()
    return _test_gen_graph


# For backwards compatibility
test_gen_graph = None  # Will be set on first use


# =============================================================================
# Public API
# =============================================================================


class GenerationStats:
    """Statistics about the generation process."""

    def __init__(self, state: TestGenState):
        self.total_questions = len(state.get("questions", []))
        self.generation_calls = state.get("total_generation_calls", 0)
        self.validation_calls = state.get("total_validation_calls", 0)
        self.total_llm_calls = state.get("llm_calls_count", 0)
        self.retries_used = state.get("retries_used", 0)
        self.batches_regenerated = state.get("batches_regenerated", 0)

        # Per-difficulty stats
        self.easy_count = len(state.get("easy_batch", {}).get("questions", []))
        self.medium_count = len(state.get("medium_batch", {}).get("questions", []))
        self.hard_count = len(state.get("hard_batch", {}).get("questions", []))


async def generate_test_pool(
    subject: str,
    grade: int,
    topic_definition: str,
    num_questions: int = 30,
    max_retries: int = 2,
) -> tuple[List[Dict[str, Any]], GenerationStats]:
    """
    Generate a validated pool of test questions using LangGraph workflow.

    Args:
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        num_questions: Target number of questions (default 30)
        max_retries: Max retries per batch (default 2)

    Returns:
        Tuple of (list of validated question dicts, GenerationStats)
    """
    initial_state: TestGenState = {
        "subject": subject,
        "grade": grade,
        "topic_definition": topic_definition,
        "num_questions": num_questions,
        "max_retries": max_retries,
        "rag_context": "",
        "rag_references": [],
        "retrieved_docs": [],
        "easy_batch": {
            "difficulty": "easy",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "medium_batch": {
            "difficulty": "medium",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "hard_batch": {
            "difficulty": "hard",
            "questions": [],
            "is_valid": False,
            "attempts": 0,
            "validation_failures": [],
        },
        "questions": [],
        "existing_question_texts": [],
        "total_generation_calls": 0,
        "total_validation_calls": 0,
        "retries_used": 0,
        "batches_regenerated": 0,
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_test_gen_graph()
        final_state = await graph.ainvoke(initial_state)
        questions = final_state.get("questions", [])
        stats = GenerationStats(final_state)
        return questions, stats
    except Exception as e:
        logger.error(f"Test generation failed: {e}", exc_info=True)
        return [], GenerationStats(initial_state)
