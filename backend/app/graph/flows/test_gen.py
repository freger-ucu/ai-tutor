"""
Test Generation Flow (EP4) - Parallel Architecture with Planning.

Generates a pool of validated test questions using batch processing
with an intelligent planning phase for concept coverage.

Flow:
    retrieve_context → plan_test → retrieve_concepts → batch_generate
                                                            ↓
                                                      batch_validate
                                                            ↓
                                                      prepare_retry ──┐
                                                            ↓         │
                                                        finalize ◄────┘

Key Design:
- Planning phase: 1 LLM call to design entire test structure
- Per-concept RAG: Parallel retrieval for each identified concept
- Batch generation: All questions generated in parallel
- Solver-based validation: Independent solver validates each question (like agent.py)
- Smart retry: Up to 2 retry iterations for failed questions
"""

import asyncio
import logging
import time
from typing import TypedDict, List, Dict, Any, Optional, Literal

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.rag.utils.hybrid_retriever import get_retriever, format_context
from app.utils.json_parser import parse_json_response
from app.config import settings, LLMProvider
from app.prompts.test_generator import (
    build_single_question_prompt,
    build_planner_prompt,
    TEST_GENERATOR_SYSTEM_PROMPT,
    TEST_PLANNER_SYSTEM_PROMPT,
)
from app.services.solver import validate_question
from ..shared.rag_node import create_rag_node, RAGConfig
from ..shared.cpu_validators import validate_single_question

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

TARGET_QUESTION_COUNT = 12
MAX_RETRY_ITERATIONS = 1
MAX_CONCURRENT_LLM = 1 if settings.llm_provider == LLMProvider.GEMINI else 10
MAX_CONCURRENT_RAG = 5


# =============================================================================
# Data Types
# =============================================================================


class QuestionSpec(TypedDict):
    """Specification for a question from planner."""
    spec_id: int
    question_type: Literal["single_choice", "multiple_choice", "open"]
    concept: str  # What concept to assess
    focus: str    # Specific aspect to test


class TestPlan(TypedDict):
    """Output of planning phase."""
    concepts: List[str]
    question_specs: List[QuestionSpec]
    rationale: str


class GenerationResult(TypedDict):
    """Result of generating a single question."""
    spec_id: int
    question: Optional[Dict[str, Any]]
    success: bool
    error: Optional[str]


class FailedQuestion(TypedDict):
    """A question that failed validation."""
    spec_id: int
    reason: str


# =============================================================================
# State Definition
# =============================================================================


class TestGenState(TypedDict, total=False):
    """State for parallel test generation flow."""

    # === INPUT ===
    subject: str
    grade: int
    topic_definition: str
    level: str  # "weak" | "medium" | "strong" - for prompt guidance

    # === TOPIC RAG (retrieved once at start) ===
    rag_context: str
    rag_references: List[Dict[str, Any]]

    # === PLANNING ===
    test_plan: Optional[TestPlan]
    concepts: List[str]
    concept_contexts: Dict[str, str]  # concept → RAG context

    # === BATCH PROCESSING ===
    pending_specs: List[QuestionSpec]
    generated_questions: List[GenerationResult]

    # === RETRY ===
    retry_count: int
    failed_specs: List[FailedQuestion]

    # === OUTPUT ===
    validated_questions: List[Dict[str, Any]]
    failed_questions: List[FailedQuestion]

    # === STATISTICS ===
    total_generated: int
    total_passed: int
    total_failed: int
    llm_calls_count: int
    planning_time_ms: int
    generation_time_ms: int
    validation_time_ms: int

    # === METADATA ===
    error_message: Optional[str]


# =============================================================================
# RAG Node (lazy initialization for topic context)
# =============================================================================

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


# =============================================================================
# Node: Retrieve Context (Topic RAG)
# =============================================================================


async def retrieve_context_node(state: TestGenState) -> Dict[str, Any]:
    """Retrieve RAG context for the topic (used for planning and fallback)."""
    logger.info(f"Retrieving context for topic: {state.get('topic_definition', '')[:50]}...")

    rag_node = _get_test_gen_rag_node()
    rag_result = await rag_node(state)

    return {
        **rag_result,
        "validated_questions": [],
        "failed_questions": [],
        "failed_specs": [],
        "total_generated": 0,
        "total_passed": 0,
        "total_failed": 0,
        "llm_calls_count": 0,
        "retry_count": 0,
        "planning_time_ms": 0,
        "generation_time_ms": 0,
        "validation_time_ms": 0,
    }


# =============================================================================
# Node: Plan Test
# =============================================================================


@trace_chain(name="plan_test")
async def plan_test_node(state: TestGenState) -> Dict[str, Any]:
    """
    Plan test structure using LLM.

    Identifies key concepts and creates question specifications.
    Difficulty is NOT determined here - it's classified post-factum.
    """
    start_time = time.time()

    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic = state.get("topic_definition", "")
    context = state.get("rag_context", "")
    level = state.get("level", "medium")

    logger.info(f"Planning test: {TARGET_QUESTION_COUNT} questions, level={level}")

    client = get_llm_client()

    prompt = build_planner_prompt(
        subject=subject,
        grade=grade,
        topic_definition=topic,
        context=context,
        level=level,
    )

    response = await client.generate(
        prompt=f"{TEST_PLANNER_SYSTEM_PROMPT}\n\n{prompt}",
        temperature=0.3,
        max_tokens=3000,
        json_mode=True,
    )

    parsed = parse_json_response(
        response,
        fallback=_generate_fallback_plan(topic),
        context="TestPlanner",
    )

    # Normalize and validate specs
    question_specs = parsed.get("question_specs", [])
    concepts = parsed.get("concepts", [topic])

    normalized_specs: List[QuestionSpec] = []
    for i, spec in enumerate(question_specs):
        normalized_specs.append({
            "spec_id": spec.get("spec_id", i + 1),
            "question_type": spec.get("question_type", "single_choice"),
            "concept": spec.get("concept", topic),
            "focus": spec.get("focus", ""),
        })

    # If planner didn't produce enough specs, add fallback
    if len(normalized_specs) < TARGET_QUESTION_COUNT:
        logger.warning(f"Planner produced {len(normalized_specs)} specs, need {TARGET_QUESTION_COUNT}")
        normalized_specs.extend(
            _generate_fallback_specs(
                topic=topic,
                count=TARGET_QUESTION_COUNT - len(normalized_specs),
                start_id=len(normalized_specs) + 1,
            )
        )

    test_plan: TestPlan = {
        "concepts": concepts,
        "question_specs": normalized_specs,
        "rationale": parsed.get("rationale", ""),
    }

    planning_time = int((time.time() - start_time) * 1000)
    logger.info(f"Test plan created in {planning_time}ms: {len(normalized_specs)} specs, concepts: {concepts}")

    return {
        "test_plan": test_plan,
        "pending_specs": normalized_specs,
        "concepts": concepts,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
        "planning_time_ms": planning_time,
    }


def _generate_fallback_plan(topic: str) -> Dict[str, Any]:
    """Generate fallback plan if LLM fails."""
    specs = _generate_fallback_specs(topic, TARGET_QUESTION_COUNT, 1)
    return {
        "concepts": [topic],
        "question_specs": specs,
        "rationale": "Fallback plan (LLM planning failed)",
    }


def _generate_fallback_specs(
    topic: str,
    count: int,
    start_id: int,
) -> List[QuestionSpec]:
    """Generate fallback specs with balanced type distribution."""
    import random
    specs: List[QuestionSpec] = []

    # Target distribution: ~50% single_choice, ~20% multiple_choice, ~30% open
    types = (
        ["single_choice"] * 6 +
        ["multiple_choice"] * 2 +
        ["open"] * 4
    )
    random.shuffle(types)

    for i in range(count):
        q_type = types[i % len(types)]
        specs.append({
            "spec_id": start_id + i,
            "question_type": q_type,
            "concept": topic,
            "focus": "",
        })

    return specs


# =============================================================================
# Node: Retrieve Concepts (Per-Concept RAG)
# =============================================================================


@trace_chain(name="retrieve_concepts")
async def retrieve_concepts_node(state: TestGenState) -> Dict[str, Any]:
    """
    Retrieve RAG context for each concept identified by planner.

    Parallel retrieval for all concepts to provide targeted context
    for question generation.
    """
    start_time = time.time()

    concepts = state.get("concepts", [])
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    base_context = state.get("rag_context", "")

    if not concepts:
        logger.warning("No concepts to retrieve, using base context")
        return {"concept_contexts": {}}

    logger.info(f"Retrieving RAG context for {len(concepts)} concepts")

    retriever = get_retriever()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_RAG)

    async def retrieve_for_concept(concept: str) -> tuple:
        async with semaphore:
            try:
                docs = await retriever.retrieve(
                    query=concept,
                    subject=subject,
                    grade=grade,
                    top_k=3,
                )
                context, _ = format_context(docs, max_chars=4000, subject=subject)
                return concept, context if context else base_context
            except Exception as e:
                logger.error(f"RAG failed for concept '{concept}': {e}")
                return concept, base_context

    results = await asyncio.gather(*[retrieve_for_concept(c) for c in concepts])
    concept_contexts = {concept: ctx for concept, ctx in results}

    retrieval_time = int((time.time() - start_time) * 1000)
    logger.info(f"Retrieved context for {len(concept_contexts)} concepts in {retrieval_time}ms")

    return {"concept_contexts": concept_contexts}


# =============================================================================
# Node: Batch Generate
# =============================================================================


@trace_chain(name="batch_generate")
async def batch_generate_node(state: TestGenState) -> Dict[str, Any]:
    """
    Generate all pending questions in parallel.

    Uses concept-specific context for each question.
    Difficulty is NOT set here - classified post-factum.
    """
    start_time = time.time()

    pending_specs = state.get("pending_specs", [])
    concept_contexts = state.get("concept_contexts", {})
    base_context = state.get("rag_context", "")
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    topic = state.get("topic_definition", "")
    level = state.get("level", "medium")

    if not pending_specs:
        logger.warning("No pending specs to generate")
        return {"generated_questions": [], "pending_specs": []}

    logger.info(f"Batch generating {len(pending_specs)} questions")

    client = get_llm_client()
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM)

    async def generate_one(spec: QuestionSpec) -> GenerationResult:
        async with semaphore:
            try:
                # Get concept-specific context
                context = concept_contexts.get(spec["concept"], base_context)

                # Pass actual question type for differentiated prompts
                # single_choice: 4 options, 1 correct (correct_answer_index)
                # multiple_choice: 4 options, 2-3 correct (correct_answer_indices)
                # open: no options, free text answer
                prompt = build_single_question_prompt(
                    subject=subject,
                    grade=grade,
                    topic=topic,
                    context=context,
                    question_type=spec["question_type"],
                    concept=spec["concept"],
                    focus=spec["focus"],
                    level=level,
                )

                # Token limits per question type (increased to prevent truncation)
                TOKEN_LIMITS = {
                    "single_choice": 2500,
                    "multiple_choice": 2500,
                    "open": 3500,
                }
                max_tokens = TOKEN_LIMITS.get(spec["question_type"], 2500)

                response = await client.generate(
                    prompt=f"{TEST_GENERATOR_SYSTEM_PROMPT}\n\n{prompt}",
                    temperature=0.7,
                    max_tokens=max_tokens,
                    json_mode=True,
                )

                parsed = parse_json_response(
                    response,
                    fallback=None,
                    context=f"TestGen-{spec['spec_id']}",
                )

                if parsed is None or not parsed.get("question"):
                    # Log raw response for debugging
                    response_preview = response[:500] if response else "(empty)"
                    logger.info(
                        f"[GEN] spec_id={spec['spec_id']} - JSON parse failed | "
                        f"type={spec['question_type']}, raw={response_preview}"
                    )
                    return {
                        "spec_id": spec["spec_id"],
                        "question": None,
                        "success": False,
                        "error": f"Empty or invalid JSON response: {response_preview[:100]}",
                    }

                # Handle wrong format: LLM returned test structure instead of single question
                if "questions" in parsed and isinstance(parsed.get("questions"), list):
                    questions_list = parsed["questions"]
                    if questions_list:
                        parsed = questions_list[0]  # Take first question
                        logger.info(f"[GEN] spec_id={spec['spec_id']} - Extracted from nested 'questions' array")
                    else:
                        return {
                            "spec_id": spec["spec_id"],
                            "question": None,
                            "success": False,
                            "error": "LLM returned empty questions array",
                        }

                # Handle wrong format: answer_options instead of options
                if "answer_options" in parsed and "options" not in parsed:
                    answer_opts = parsed["answer_options"]
                    if isinstance(answer_opts, list) and answer_opts:
                        # Convert answer_options format to options format
                        parsed["options"] = [opt.get("answer", str(opt)) for opt in answer_opts]
                        # Find correct answer indices
                        correct_indices = [i for i, opt in enumerate(answer_opts) if opt.get("correct", False)]

                        if not correct_indices:
                            logger.warning(
                                f"[GEN] spec_id={spec['spec_id']} - answer_options has NO correct answer! "
                                f"All options marked correct=false"
                            )
                            # Don't default - let CPU validation catch this
                        elif spec["question_type"] == "single_choice":
                            # Single choice: use first correct answer
                            parsed["correct_answer_index"] = correct_indices[0]
                            logger.info(f"[GEN] spec_id={spec['spec_id']} - Converted answer_options to single_choice")
                        elif spec["question_type"] == "multiple_choice":
                            # Multiple choice: use all correct answers
                            parsed["correct_answer_indices"] = correct_indices
                            logger.info(f"[GEN] spec_id={spec['spec_id']} - Converted answer_options to multiple_choice with {len(correct_indices)} correct")

                # Normalize the question (difficulty will be set by classify_difficulty_node)
                question = parsed
                question["type"] = spec["question_type"]
                question["spec_id"] = spec["spec_id"]
                question["concept"] = spec["concept"]

                # Ensure correct_answer_index(es) for choice questions
                if spec["question_type"] == "single_choice":
                    # Single choice: exactly 1 correct answer (correct_answer_index as int)
                    if "correct_answer_index" in question:
                        idx = question["correct_answer_index"]
                        if not isinstance(idx, int) or idx < 0 or idx > 3:
                            logger.warning(f"[GEN] spec_id={spec['spec_id']} - Invalid correct_answer_index: {idx}")
                            del question["correct_answer_index"]
                    elif "correct_answer" in question:
                        answer_letter = str(question["correct_answer"]).strip().upper()
                        letter_to_index = {"A": 0, "B": 1, "C": 2, "D": 3}
                        if answer_letter in letter_to_index:
                            question["correct_answer_index"] = letter_to_index[answer_letter]
                        else:
                            logger.warning(f"[GEN] spec_id={spec['spec_id']} - Invalid correct_answer letter: {answer_letter}")

                elif spec["question_type"] == "multiple_choice":
                    # Multiple choice: 2-3 correct answers (correct_answer_indices as list)
                    if "correct_answer_indices" in question:
                        indices = question["correct_answer_indices"]
                        if isinstance(indices, list) and len(indices) >= 2:
                            valid_indices = [i for i in indices if isinstance(i, int) and 0 <= i <= 3]
                            if len(valid_indices) >= 2:
                                question["correct_answer_indices"] = valid_indices
                            else:
                                logger.warning(f"[GEN] spec_id={spec['spec_id']} - Invalid correct_answer_indices: {indices}")
                                del question["correct_answer_indices"]
                        else:
                            logger.warning(f"[GEN] spec_id={spec['spec_id']} - Multiple choice needs 2+ answers: {indices}")
                            del question["correct_answer_indices"]
                    elif "correct_answer_index" in question:
                        # LLM gave single index instead of list - convert but warn
                        idx = question["correct_answer_index"]
                        logger.warning(f"[GEN] spec_id={spec['spec_id']} - Multiple choice got single index {idx}, expected list")
                        # Don't convert - let validation fail, this is a generation error

                return {
                    "spec_id": spec["spec_id"],
                    "question": question,
                    "success": True,
                    "error": None,
                }

            except Exception as e:
                logger.error(f"Generation failed for spec {spec['spec_id']}: {e}")
                return {
                    "spec_id": spec["spec_id"],
                    "question": None,
                    "success": False,
                    "error": str(e),
                }

    results = await asyncio.gather(*[generate_one(spec) for spec in pending_specs])

    successful = sum(1 for r in results if r["success"])
    generation_time = int((time.time() - start_time) * 1000)

    logger.info(f"Batch generation complete in {generation_time}ms: {successful}/{len(pending_specs)} successful")

    return {
        "generated_questions": list(results),
        "pending_specs": [],
        "total_generated": state.get("total_generated", 0) + len(results),
        "llm_calls_count": state.get("llm_calls_count", 0) + len(pending_specs),
        "generation_time_ms": state.get("generation_time_ms", 0) + generation_time,
    }


# =============================================================================
# Node: Batch Validate (Hybrid Approach)
# =============================================================================


@trace_chain(name="batch_validate")
async def batch_validate_node(state: TestGenState) -> Dict[str, Any]:
    """
    Validate generated questions using hybrid approach.

    1. CPU validation (format, dedup) - instant
    2. LLM validation (parallel):
       - MC: reuses concept_context (no extra RAG)
       - Open: retrieves fresh context per question
    """
    start_time = time.time()

    generated = state.get("generated_questions", [])
    concept_contexts = state.get("concept_contexts", {})
    base_context = state.get("rag_context", "")
    subject = state.get("subject", "")
    grade = state.get("grade", 9)

    validated = state.get("validated_questions", [])
    existing_texts = {q.get("question", "") for q in validated}

    if not generated:
        logger.warning("No generated questions to validate")
        return {"failed_specs": []}

    logger.info(f"Batch validating {len(generated)} questions")

    # ═══════════════════════════════════════════════════════
    # Phase 1: CPU Validation (instant)
    # ═══════════════════════════════════════════════════════
    cpu_passed: List[Dict[str, Any]] = []
    cpu_failed: List[FailedQuestion] = []

    for gen_result in generated:
        if not gen_result.get("success") or not gen_result.get("question"):
            cpu_failed.append({
                "spec_id": gen_result.get("spec_id", 0),
                "reason": gen_result.get("error", "Generation failed"),
            })
            logger.info(f"[CPU] spec_id={gen_result.get('spec_id')} - Generation failed: {gen_result.get('error')}")
            continue

        question = gen_result["question"]
        is_valid, reason = validate_single_question(question, existing_texts)

        if is_valid:
            existing_texts.add(question.get("question", ""))
            cpu_passed.append(question)
            logger.debug(f"[CPU] spec_id={question.get('spec_id')} - PASSED")
        else:
            cpu_failed.append({
                "spec_id": question.get("spec_id", 0),
                "reason": f"CPU: {reason}",
            })
            logger.info(
                f"[CPU] spec_id={question.get('spec_id')} - REJECTED: {reason} | "
                f"type={question.get('type')}, options={len(question.get('options', []))}, "
                f"q={question.get('question', '')[:50]}..."
            )

    logger.info(f"CPU validation: {len(cpu_passed)} passed, {len(cpu_failed)} failed")

    # ═══════════════════════════════════════════════════════
    # Phase 2: LLM Validation (parallel, type-specific)
    # ═══════════════════════════════════════════════════════
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM)

    async def validate_one(question: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unified validation using solver-based approach.

        Solver independently solves the question, then compares with expected answer.
        Same flow for MC and Open questions.
        """
        async with semaphore:
            try:
                q_type = question.get("type", "open")

                # Unified validation (self-contained RAG, like agent.py)
                result = await validate_question(
                    question_text=question.get("question", ""),
                    question_type=q_type,
                    subject=subject,
                    grade=grade,
                    options=question.get("options"),
                    expected_index=question.get("correct_answer_index"),
                    expected_indices=question.get("correct_answer_indices"),
                    expected_answer=question.get("explanation"),
                )

                logger.debug(
                    f"[Validate] spec_id={question.get('spec_id')} type={q_type} - "
                    f"valid={result.is_valid}, solver={result.solver_answer}, "
                    f"expected={result.expected_answer}"
                )

                return {
                    "question": question,
                    "is_valid": result.is_valid,
                    "reason": result.reason,
                    "confidence": result.confidence,
                }
            except Exception as e:
                logger.error(f"Validation failed for question: {e}")
                return {"question": question, "is_valid": False, "reason": str(e)}

    # Run all validations in parallel
    validation_results = await asyncio.gather(
        *[validate_one(q) for q in cpu_passed],
        return_exceptions=True
    )

    # Collect results
    passed_questions: List[Dict[str, Any]] = []
    llm_failed: List[FailedQuestion] = []

    for result in validation_results:
        if isinstance(result, Exception):
            logger.error(f"Validation exception: {result}")
            continue
        if result["is_valid"]:
            passed_questions.append(result["question"])
        else:
            llm_failed.append({
                "spec_id": result["question"].get("spec_id", 0),
                "reason": f"LLM: {result['reason']}",
            })

    validation_time = int((time.time() - start_time) * 1000)
    all_failed = cpu_failed + llm_failed

    logger.info(
        f"Validation complete in {validation_time}ms: "
        f"{len(passed_questions)} passed, {len(all_failed)} failed"
    )

    return {
        "validated_questions": validated + passed_questions,
        "failed_specs": all_failed,
        "generated_questions": [],  # Clear for next iteration
        "total_passed": state.get("total_passed", 0) + len(passed_questions),
        "total_failed": state.get("total_failed", 0) + len(all_failed),
        "llm_calls_count": state.get("llm_calls_count", 0) + len(cpu_passed),
        "validation_time_ms": state.get("validation_time_ms", 0) + validation_time,
    }


# =============================================================================
# Node: Prepare Retry
# =============================================================================


def prepare_retry_node(state: TestGenState) -> Dict[str, Any]:
    """
    Prepare failed specs for retry.

    Finds original specs for failed questions and queues them
    for another generation attempt (max 1 iteration).
    """
    retry_count = state.get("retry_count", 0)
    failed_specs = state.get("failed_specs", [])
    test_plan = state.get("test_plan") or {}

    if retry_count >= MAX_RETRY_ITERATIONS:
        logger.info(f"Max retry iterations ({MAX_RETRY_ITERATIONS}) reached")
        # Move remaining failed to final failed list
        return {
            "pending_specs": [],
            "failed_questions": state.get("failed_questions", []) + failed_specs,
            "failed_specs": [],
        }

    if not failed_specs:
        logger.info("No failed specs to retry")
        return {"pending_specs": []}

    # Find original specs for failed questions
    original_specs = {s["spec_id"]: s for s in test_plan.get("question_specs", [])}
    failed_ids = {f["spec_id"] for f in failed_specs}

    retry_specs: List[QuestionSpec] = []
    for spec_id in failed_ids:
        if spec_id in original_specs:
            # Create modified spec for retry with new ID
            original = original_specs[spec_id]
            retry_specs.append({
                "spec_id": spec_id + 1000 * (retry_count + 1),
                "question_type": original["question_type"],
                "concept": original["concept"],
                "focus": f"{original.get('focus', '')} (retry {retry_count + 1})".strip(),
            })

    logger.info(f"Prepared {len(retry_specs)} specs for retry iteration {retry_count + 1}")

    return {
        "pending_specs": retry_specs,
        "retry_count": retry_count + 1,
        "failed_specs": [],  # Clear for next iteration
    }


def should_retry(state: TestGenState) -> Literal["batch_generate", "classify_difficulty"]:
    """Decide whether to retry or proceed to difficulty classification."""
    pending_specs = state.get("pending_specs", [])

    if pending_specs:
        return "batch_generate"
    return "classify_difficulty"


# =============================================================================
# Node: Classify Difficulty (Post-factum)
# =============================================================================


@trace_chain(name="classify_difficulty")
async def classify_difficulty_node(state: TestGenState) -> Dict[str, Any]:
    """
    Classify difficulty for all validated questions using LLM.

    Uses BATCH classification for better difficulty distribution.
    The LLM sees all questions together and is instructed to use all three levels.
    """
    from app.prompts.test_generator import build_batch_difficulty_classifier_prompt

    start_time = time.time()

    questions = state.get("validated_questions", [])
    subject = state.get("subject", "")
    grade = state.get("grade", 9)

    if not questions:
        logger.warning("No questions to classify")
        return {}

    logger.info(f"Classifying difficulty for {len(questions)} questions (batch mode)")

    client = get_llm_client()

    # Build batch classification prompt
    prompt = build_batch_difficulty_classifier_prompt(
        subject=subject,
        grade=grade,
        questions=questions,
    )

    try:
        response = await client.generate(
            prompt=prompt,
            temperature=0.1,  # Small temperature for variety
            max_tokens=2000,  # Enough for all classifications
            json_mode=True,
        )

        result = parse_json_response(
            response,
            fallback={"classifications": []},
            context="BatchDifficultyClassifier",
        )

        classifications = result.get("classifications", [])

        # Build a map of spec_id -> difficulty
        difficulty_map: Dict[int, str] = {}
        for c in classifications:
            spec_id = c.get("spec_id")
            difficulty = c.get("difficulty", "medium").lower()
            if difficulty not in {"easy", "medium", "hard"}:
                difficulty = "medium"
            if spec_id is not None:
                difficulty_map[spec_id] = difficulty
                logger.debug(
                    f"[CLASSIFY] spec_id={spec_id} - {difficulty} | "
                    f"{c.get('reasoning', '')[:50]}"
                )

        # Apply classifications to questions
        for q in questions:
            spec_id = q.get("spec_id")
            if spec_id in difficulty_map:
                q["difficulty"] = difficulty_map[spec_id]
            else:
                # Fallback for unclassified questions
                q["difficulty"] = "medium"
                logger.warning(f"[CLASSIFY] spec_id={spec_id} not in batch result, defaulting to medium")

    except Exception as e:
        logger.error(f"Batch difficulty classification failed: {e}")
        # Fallback: distribute difficulties evenly
        logger.info("Using fallback distribution: ~33% each")
        n = len(questions)
        for i, q in enumerate(questions):
            if i < n // 3:
                q["difficulty"] = "easy"
            elif i < 2 * n // 3:
                q["difficulty"] = "medium"
            else:
                q["difficulty"] = "hard"

    classification_time = int((time.time() - start_time) * 1000)
    logger.info(f"Difficulty classification complete in {classification_time}ms")

    # Log distribution
    easy = sum(1 for q in questions if q.get("difficulty") == "easy")
    medium = sum(1 for q in questions if q.get("difficulty") == "medium")
    hard = sum(1 for q in questions if q.get("difficulty") == "hard")
    logger.info(f"Difficulty distribution: easy={easy}, medium={medium}, hard={hard}")

    return {
        "validated_questions": questions,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,  # Only 1 batch call now
    }


# =============================================================================
# Node: Finalize
# =============================================================================


def finalize_node(state: TestGenState) -> Dict[str, Any]:
    """
    Finalize the test generation.

    Logs statistics and returns final state.
    """
    validated = state.get("validated_questions", [])

    # Count by difficulty
    easy_count = sum(1 for q in validated if q.get("difficulty") == "easy")
    medium_count = sum(1 for q in validated if q.get("difficulty") == "medium")
    hard_count = sum(1 for q in validated if q.get("difficulty") == "hard")

    # Count by type
    single_count = sum(1 for q in validated if q.get("type") == "single_choice")
    multiple_count = sum(1 for q in validated if q.get("type") == "multiple_choice")
    open_count = sum(1 for q in validated if q.get("type") == "open")

    logger.info(
        f"Test generation complete: {len(validated)} questions "
        f"(easy={easy_count}, medium={medium_count}, hard={hard_count}, "
        f"single_choice={single_count}, multiple_choice={multiple_count}, open={open_count})"
    )
    logger.info(
        f"Stats: generated={state.get('total_generated', 0)}, "
        f"passed={state.get('total_passed', 0)}, "
        f"failed={state.get('total_failed', 0)}, "
        f"llm_calls={state.get('llm_calls_count', 0)}, "
        f"retries={state.get('retry_count', 0)}"
    )
    logger.info(
        f"Timing: planning={state.get('planning_time_ms', 0)}ms, "
        f"generation={state.get('generation_time_ms', 0)}ms, "
        f"validation={state.get('validation_time_ms', 0)}ms"
    )

    return {}


# =============================================================================
# Build Graph
# =============================================================================


def build_test_gen_graph():
    """
    Build the LangGraph workflow for parallel test generation.

    Flow:
        retrieve_context → plan_test → retrieve_concepts → batch_generate
                                                                ↓
                                                          batch_validate
                                                                ↓
                                                          prepare_retry ──┐
                                                                ↓         │
                                                    classify_difficulty ◄─┘
                                                                ↓
                                                            finalize
    """
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(TestGenState)

    # Add nodes
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("plan_test", plan_test_node)
    workflow.add_node("retrieve_concepts", retrieve_concepts_node)
    workflow.add_node("batch_generate", batch_generate_node)
    workflow.add_node("batch_validate", batch_validate_node)
    workflow.add_node("prepare_retry", prepare_retry_node)
    workflow.add_node("classify_difficulty", classify_difficulty_node)
    workflow.add_node("finalize", finalize_node)

    # Setup edges
    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "plan_test")
    workflow.add_edge("plan_test", "retrieve_concepts")
    workflow.add_edge("retrieve_concepts", "batch_generate")
    workflow.add_edge("batch_generate", "batch_validate")
    workflow.add_edge("batch_validate", "prepare_retry")

    # Conditional retry loop - goes to classify_difficulty when done
    workflow.add_conditional_edges(
        "prepare_retry",
        should_retry,
        {
            "batch_generate": "batch_generate",
            "classify_difficulty": "classify_difficulty",
        },
    )

    workflow.add_edge("classify_difficulty", "finalize")
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
test_gen_graph = None


# =============================================================================
# Public API
# =============================================================================


class GenerationStats:
    """Statistics about the parallel generation process."""

    def __init__(self, state: TestGenState):
        self.total_questions = len(state.get("validated_questions", []))
        self.total_generated = state.get("total_generated", 0)
        self.total_passed = state.get("total_passed", 0)
        self.total_failed = state.get("total_failed", 0)
        self.total_llm_calls = state.get("llm_calls_count", 0)

        # Per-difficulty stats
        validated = state.get("validated_questions", [])
        self.easy_count = sum(1 for q in validated if q.get("difficulty") == "easy")
        self.medium_count = sum(1 for q in validated if q.get("difficulty") == "medium")
        self.hard_count = sum(1 for q in validated if q.get("difficulty") == "hard")

        # Per-type stats
        self.single_choice_count = sum(1 for q in validated if q.get("type") == "single_choice")
        self.multiple_choice_count = sum(1 for q in validated if q.get("type") == "multiple_choice")
        self.open_count = sum(1 for q in validated if q.get("type") == "open")

        # Timing stats
        self.planning_time_ms = state.get("planning_time_ms", 0)
        self.generation_time_ms = state.get("generation_time_ms", 0)
        self.validation_time_ms = state.get("validation_time_ms", 0)
        self.retry_count = state.get("retry_count", 0)

        # Planning info
        test_plan = state.get("test_plan") or {}
        self.concepts_covered = test_plan.get("concepts", [])

        # Failed questions for debugging
        self.failed_questions = state.get("failed_questions", [])


async def generate_test_pool(
    subject: str,
    grade: int,
    topic_definition: str,
    level: str = "medium",
) -> tuple[List[Dict[str, Any]], GenerationStats]:
    """
    Generate a validated pool of test questions using parallel LangGraph workflow.

    Architecture:
    1. Retrieve RAG context (1 call)
    2. Plan test structure (1 LLM call) - creates 12 question specs
    3. Retrieve per-concept context (N parallel RAG)
    4. Batch generate questions (N parallel LLM)
    5. Batch validate questions (hybrid: MC reuse context, Open fresh RAG)
    6. Retry failed questions (max 1 iteration)
    7. Classify difficulty post-factum (N parallel LLM)

    Args:
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        topic_definition: Topic description
        level: Student level for prompt guidance ("weak", "medium", "strong")

    Returns:
        Tuple of (list of validated question dicts, GenerationStats)
    """
    initial_state: TestGenState = {
        "subject": subject,
        "grade": grade,
        "topic_definition": topic_definition,
        "level": level,
        "rag_context": "",
        "rag_references": [],
        "test_plan": None,
        "concepts": [],
        "concept_contexts": {},
        "pending_specs": [],
        "generated_questions": [],
        "retry_count": 0,
        "failed_specs": [],
        "validated_questions": [],
        "failed_questions": [],
        "total_generated": 0,
        "total_passed": 0,
        "total_failed": 0,
        "llm_calls_count": 0,
        "planning_time_ms": 0,
        "generation_time_ms": 0,
        "validation_time_ms": 0,
        "error_message": None,
    }

    try:
        graph = get_test_gen_graph()
        # New flow has much lower recursion limit
        # Base nodes (4) + retry iterations (2) * nodes per iteration (3) + buffer
        recursion_limit = 20

        final_state = await graph.ainvoke(
            initial_state,
            config={"recursion_limit": recursion_limit}
        )

        questions = final_state.get("validated_questions", [])
        stats = GenerationStats(final_state)

        return questions, stats

    except Exception as e:
        logger.error(f"Test generation failed: {e}", exc_info=True)
        return [], GenerationStats(initial_state)
