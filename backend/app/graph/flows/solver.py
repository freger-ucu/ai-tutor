"""
Solver Flow (EP7) V2.

V2: Integrated patterns from agent.py:
1. Option-wise retrieval: retrieves separately for stem+each_option
2. Support scoring: scores how well each option is supported by context
3. Verify loop: checks answer support, refines retrieval if needed (max 2 iterations)

Flow:
    retrieve_rag → retrieve_options → support_scoring → generate_answer → verify
                                                                           ↓
                                                                     [refine_retrieval] (conditional)
                                                                           ↓
                                                                          END
"""

import asyncio
import logging
import re
from typing import TypedDict, List, Dict, Any, Optional, Tuple

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import generate_json_safe, get_llm_client
from app.rag.utils.hybrid_retriever import get_retriever, format_context
from app.utils.json_parser import parse_json_response
# Import prompts from shared location (avoids circular import)
from app.prompts.solver import SUPPORT_SCORING_PROMPT, VERIFY_PROMPT

logger = logging.getLogger(__name__)


# Lazy import for unified_generate to avoid circular import
_unified_generate_cache = None


def _get_unified_generate():
    """Lazy import to avoid circular import with unified_generate."""
    global _unified_generate_cache
    if _unified_generate_cache is None:
        from app.rag.nodes.unified_generate import (
            SUBJECT_PROMPTS,
            DEFAULT_PROMPT,
            _format_options,
        )
        _unified_generate_cache = (SUBJECT_PROMPTS, DEFAULT_PROMPT, _format_options)
    return _unified_generate_cache


# =============================================================================
# State Definition
# =============================================================================


class SolverState(TypedDict, total=False):
    """State for solver flow V2."""

    # Input
    question_id: str
    question_text: str
    subject: str
    grade: int
    answers: List[str]
    correct_indices: List[int]  # For evaluation only

    # V2: Parsed question
    stem: str  # Question without options
    parsed_options: Dict[int, str]  # Index -> option text

    # RAG output (general)
    rag_context: str
    rag_references: List[Dict[str, Any]]
    retrieved_docs: List[Dict[str, Any]]
    matched_topics: List[Dict[str, Any]]

    # V2: Option-wise retrieval
    option_contexts: Dict[int, str]  # option_index -> context
    option_docs: Dict[int, List[Dict[str, Any]]]  # option_index -> docs

    # V2: Support scoring
    option_scores: Dict[int, float]  # option_index -> support score (0-10)
    suggested_best: Optional[int]  # Best option from support scoring

    # Generation output
    answer_index: int
    confidence: float
    reasoning: str
    rule_found: str
    source_reference: Dict[str, Any]

    # V2: Verification loop
    iteration: int
    verification: Optional[Dict[str, Any]]  # {supported, confidence, missing_terms}
    max_iterations: int

    # Metadata
    llm_calls_count: int
    error_message: Optional[str]
    trace_id: str


# =============================================================================
# Utility Functions
# =============================================================================


def _parse_question_stem(question_text: str, answers: List[str]) -> str:
    """Extract question stem (text without options)."""
    # Try to find where options start
    lines = question_text.split('\n')
    stem_lines = []

    for line in lines:
        stripped = line.strip()
        # Check if line starts with option pattern
        if re.match(r'^[ABCD0-3]\)', stripped) or stripped.startswith('Варіанти:'):
            break
        if stripped:
            stem_lines.append(line)

    stem = '\n'.join(stem_lines).strip()

    # If stem is same as full question, just return it
    if not stem or stem == question_text:
        return question_text

    return stem


def _parse_support_scores(response: str) -> Tuple[Dict[int, float], Optional[int]]:
    """Parse support scoring response."""
    try:
        data = parse_json_response(response, {}, "SupportScoring")
        scores = data.get("scores", {})
        best = data.get("best", None)

        # Normalize scores to int keys
        float_scores = {}
        for k, v in scores.items():
            try:
                idx = int(k)
                if 0 <= idx <= 3:
                    float_scores[idx] = float(v) if v else 0.0
            except (ValueError, TypeError):
                continue

        # Parse best
        if best is not None:
            try:
                best = int(best)
                if not (0 <= best <= 3):
                    best = None
            except (ValueError, TypeError):
                best = None

        return float_scores, best
    except Exception as e:
        logger.warning(f"Failed to parse support scores: {e}")
        return {}, None


def _parse_verification(response: str) -> Dict[str, Any]:
    """Parse verification response."""
    try:
        data = parse_json_response(response, {}, "Verification")
        return {
            "supported": data.get("supported", True),
            "confidence": data.get("confidence", 5),
            "missing_terms": data.get("missing_terms", []),
            "reasoning": data.get("reasoning", "")
        }
    except Exception as e:
        logger.warning(f"Failed to parse verification: {e}")
        return {"supported": True, "confidence": 5, "missing_terms": [], "reasoning": ""}


# =============================================================================
# Graph Nodes
# =============================================================================


@trace_chain(name="retrieve_rag")
async def retrieve_rag_node(state: SolverState) -> Dict[str, Any]:
    """
    Retrieve RAG context for the question stem.

    Uses hybrid retrieval (BM25 + vector) with RRF fusion.
    """
    question_text = state.get("question_text", "")
    answers = state.get("answers", [])
    subject = state.get("subject", "")
    grade = state.get("grade", 9)

    # Parse stem
    stem = _parse_question_stem(question_text, answers)
    parsed_options = {i: opt for i, opt in enumerate(answers)}

    # Retrieve for stem
    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=stem,
        subject=subject,
        grade=grade,
        top_k=5,
    )

    # Format context
    context, references = format_context(docs, max_chars=6000, subject=subject)

    return {
        "stem": stem,
        "parsed_options": parsed_options,
        "rag_context": context,
        "rag_references": references,
        "retrieved_docs": docs,
    }


@trace_chain(name="retrieve_options")
async def retrieve_options_node(state: SolverState) -> Dict[str, Any]:
    """
    V2: Option-wise retrieval - retrieve separately for stem+each_option.

    This helps find context that specifically supports or refutes each option.
    """
    stem = state.get("stem", "")
    parsed_options = state.get("parsed_options", {})
    subject = state.get("subject", "")
    grade = state.get("grade", 9)

    if not parsed_options:
        return {"option_contexts": {}, "option_docs": {}}

    retriever = get_retriever()

    async def retrieve_for_option(idx: int, option_text: str) -> Tuple[int, str, List[Dict]]:
        """Retrieve context for a single option."""
        query = f"{stem} {option_text}"
        docs = await retriever.retrieve(
            query=query,
            subject=subject,
            grade=grade,
            top_k=3,  # Fewer docs per option
        )
        context, _ = format_context(docs, max_chars=2000, subject=subject)
        return idx, context, docs

    # Parallel retrieval for all options
    tasks = [
        retrieve_for_option(idx, opt)
        for idx, opt in parsed_options.items()
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    option_contexts = {}
    option_docs = {}

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Option retrieval failed: {result}")
            continue
        idx, context, docs = result
        option_contexts[idx] = context
        option_docs[idx] = docs

    logger.info(f"Retrieved context for {len(option_contexts)} options")

    return {
        "option_contexts": option_contexts,
        "option_docs": option_docs,
    }


@trace_chain(name="support_scoring")
async def support_scoring_node(state: SolverState) -> Dict[str, Any]:
    """
    V2: Score how well each option is supported by retrieved context.

    Uses LLM to evaluate support scores (0-10) for each option.
    """
    stem = state.get("stem", "")
    parsed_options = state.get("parsed_options", {})
    rag_context = state.get("rag_context", "")
    subject = state.get("subject", "")

    if len(parsed_options) < 2 or not rag_context:
        return {
            "option_scores": {},
            "suggested_best": None,
            "llm_calls_count": state.get("llm_calls_count", 0),
        }

    # Truncate context for scoring (keep it focused)
    scoring_context = rag_context[:3000] if len(rag_context) > 3000 else rag_context

    # Build prompt
    prompt = SUPPORT_SCORING_PROMPT.format(
        stem=stem,
        option_0=parsed_options.get(0, ""),
        option_1=parsed_options.get(1, ""),
        option_2=parsed_options.get(2, ""),
        option_3=parsed_options.get(3, ""),
        context=scoring_context,
    )

    # Generate scores
    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        temperature=0.0,
        max_tokens=300,
    )

    option_scores, suggested_best = _parse_support_scores(response)

    logger.info(f"Support scores: {option_scores}, best: {suggested_best}")

    return {
        "option_scores": option_scores,
        "suggested_best": suggested_best,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


@trace_chain(name="generate_answer")
async def generate_answer_node(state: SolverState) -> Dict[str, Any]:
    """
    Generate answer using subject-specific expert prompts.

    V2: Uses option support scores as hints when available.
    """
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    question_text = state.get("question_text", "")
    answers = state.get("answers", [])
    context = state.get("rag_context", "")
    references = state.get("rag_references", [])
    option_scores = state.get("option_scores", {})

    # Get subject-specific prompt template (lazy import to avoid circular import)
    SUBJECT_PROMPTS, DEFAULT_PROMPT, _format_options = _get_unified_generate()
    prompt_template = SUBJECT_PROMPTS.get(subject, DEFAULT_PROMPT)

    # Build prompt
    prompt = prompt_template.format(
        context=context if context else "Контекст не знайдено.",
        subject=subject,
        grade=grade,
        question=question_text,
        options=_format_options(answers),
    )

    # V2: Add support score hint if available
    if option_scores:
        max_score = max(option_scores.values()) if option_scores else 0
        if max_score >= 7:
            best_idx = max(option_scores.items(), key=lambda x: x[1])[0]
            best_text = answers[best_idx] if best_idx < len(answers) else ""
            prompt += f"\n\nПідказка: варіант {best_idx}) {best_text[:50]} має найкраще підтвердження в контексті (score: {max_score}/10)."

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
        # V2: Fallback to highest support score if available
        if option_scores:
            answer_index = max(option_scores.items(), key=lambda x: x[1])[0]
            logger.warning(f"Invalid answer, using support score fallback: {answer_index}")
        else:
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


@trace_chain(name="verify_answer")
async def verify_answer_node(state: SolverState) -> Dict[str, Any]:
    """
    V2: Verify if answer is well-supported by context.

    Checks answer support and identifies missing terms for potential refinement.
    """
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)

    if iteration >= max_iterations:
        return {
            "verification": {"supported": True, "confidence": 5, "missing_terms": []},
        }

    question_text = state.get("question_text", "")
    answer_index = state.get("answer_index", 0)
    answers = state.get("answers", [])
    context = state.get("rag_context", "")

    if not context or len(context) < 100:
        return {
            "verification": {"supported": False, "confidence": 0, "missing_terms": []},
        }

    answer_text = answers[answer_index] if answer_index < len(answers) else ""

    # Build verify prompt
    prompt = VERIFY_PROMPT.format(
        question=question_text,
        answer=answer_index,
        answer_text=answer_text,
        context=context[:4000],  # Truncate for verification
    )

    client = get_llm_client()
    response = await client.generate(
        prompt=prompt,
        temperature=0.0,
        max_tokens=300,
    )

    verification = _parse_verification(response)

    logger.info(
        f"Verification: supported={verification['supported']}, "
        f"confidence={verification['confidence']}, "
        f"missing_terms={verification.get('missing_terms', [])}"
    )

    return {
        "verification": verification,
        "llm_calls_count": state.get("llm_calls_count", 0) + 1,
    }


@trace_chain(name="refine_retrieval")
async def refine_retrieval_node(state: SolverState) -> Dict[str, Any]:
    """
    V2: Refine retrieval with missing terms from verification.

    Adds new documents to context based on missing terms.
    """
    verification = state.get("verification", {})
    missing_terms = verification.get("missing_terms", [])
    stem = state.get("stem", "")
    subject = state.get("subject", "")
    grade = state.get("grade", 9)
    existing_docs = state.get("retrieved_docs", [])

    if not missing_terms:
        return {
            "iteration": state.get("iteration", 0) + 1,
        }

    # Build refined query with missing terms
    refined_query = f"{stem} {' '.join(missing_terms)}"

    logger.info(f"Refining retrieval with: {refined_query[:100]}...")

    # Retrieve with refined query
    retriever = get_retriever()
    new_docs = await retriever.retrieve(
        query=refined_query,
        subject=subject,
        grade=grade,
        top_k=3,
    )

    # Merge with existing (avoid duplicates by page_id)
    existing_ids = {d.get("page_id") for d in existing_docs}
    merged_docs = list(existing_docs)

    for doc in new_docs:
        if doc.get("page_id") not in existing_ids:
            merged_docs.append(doc)
            existing_ids.add(doc.get("page_id"))

    # Rebuild context
    context, references = format_context(merged_docs, max_chars=6000, subject=subject)

    logger.info(f"Refined retrieval: added {len(new_docs)} docs, total {len(merged_docs)}")

    return {
        "retrieved_docs": merged_docs,
        "rag_context": context,
        "rag_references": references,
        "iteration": state.get("iteration", 0) + 1,
    }


# =============================================================================
# Routing Functions
# =============================================================================


def should_refine(state: SolverState) -> str:
    """Decide whether to refine retrieval or finish."""
    verification = state.get("verification", {})
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 2)

    supported = verification.get("supported", True)
    confidence = verification.get("confidence", 10)
    missing_terms = verification.get("missing_terms", [])

    # Refine if: not supported, low confidence, has missing terms, haven't exceeded iterations
    if not supported and confidence < 5 and missing_terms and iteration < max_iterations:
        return "refine"

    return "end"


# =============================================================================
# Build Graph
# =============================================================================


def build_solver_graph():
    """
    Build the LangGraph workflow for question solving V2.

    Flow:
        retrieve_rag → retrieve_options → support_scoring → generate_answer → verify
                                                                               ↓
                                                                         [refine] (conditional)
                                                                               ↓
                                                                              END
    """
    # Lazy import to avoid grpcio initialization at module load (macOS mutex.cc issue)
    from langgraph.graph import StateGraph, END

    workflow = StateGraph(SolverState)

    # Add nodes
    workflow.add_node("retrieve_rag", retrieve_rag_node)
    workflow.add_node("retrieve_options", retrieve_options_node)
    workflow.add_node("support_scoring", support_scoring_node)
    workflow.add_node("generate_answer", generate_answer_node)
    workflow.add_node("verify", verify_answer_node)
    workflow.add_node("refine_retrieval", refine_retrieval_node)

    # Set entry point
    workflow.set_entry_point("retrieve_rag")

    # Main flow
    workflow.add_edge("retrieve_rag", "retrieve_options")
    workflow.add_edge("retrieve_options", "support_scoring")
    workflow.add_edge("support_scoring", "generate_answer")
    workflow.add_edge("generate_answer", "verify")

    # Conditional: verify -> refine or end
    workflow.add_conditional_edges(
        "verify",
        should_refine,
        {
            "refine": "refine_retrieval",
            "end": END
        }
    )

    # Refine loops back to support_scoring (re-evaluate with new context)
    workflow.add_edge("refine_retrieval", "support_scoring")

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
        model_used: str = "solver-graph-v2",
        option_scores: Optional[Dict[int, float]] = None,
        verification: Optional[Dict[str, Any]] = None,
    ):
        self.answer_index = answer_index
        self.confidence = confidence
        self.reasoning = reasoning
        self.references = references
        self.llm_calls = llm_calls
        self.model_used = model_used
        self.option_scores = option_scores or {}
        self.verification = verification or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer_index": self.answer_index,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "references": self.references,
            "llm_calls": self.llm_calls,
            "model_used": self.model_used,
            "option_scores": self.option_scores,
            "verification": self.verification,
        }


async def solve_question(
    question_id: str,
    question_text: str,
    subject: str,
    grade: int,
    answers: List[str],
    correct_indices: Optional[List[int]] = None,
    max_iterations: int = 2,
) -> SolverResult:
    """
    Solve a question using the LangGraph workflow V2.

    V2 Features:
    - Option-wise retrieval (retrieves for stem+each_option)
    - Support scoring (scores how well each option is supported)
    - Verify loop (checks answer, refines if needed)

    Args:
        question_id: Unique question identifier
        question_text: The question text
        subject: Subject name (Алгебра, Українська мова, etc.)
        grade: Grade level (8 or 9)
        answers: List of answer options
        correct_indices: Optional correct answer indices (for evaluation)
        max_iterations: Max verify/refine iterations (default 2)

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
        # V2 fields
        "stem": "",
        "parsed_options": {},
        "option_contexts": {},
        "option_docs": {},
        "option_scores": {},
        "suggested_best": None,
        # RAG fields
        "rag_context": "",
        "rag_references": [],
        "retrieved_docs": [],
        "matched_topics": [],
        # Output fields
        "answer_index": 0,
        "confidence": 0.0,
        "reasoning": "",
        "rule_found": "",
        "source_reference": {},
        # V2: Verification loop
        "iteration": 0,
        "verification": None,
        "max_iterations": max_iterations,
        # Metadata
        "llm_calls_count": 0,
        "error_message": None,
        "trace_id": "",
    }

    try:
        graph = get_solver_graph()
        final_state = await graph.ainvoke(initial_state)

        # Calculate confidence from verification and support scores
        verification = final_state.get("verification", {})
        option_scores = final_state.get("option_scores", {})

        confidence = final_state.get("confidence", 0.5)
        if verification:
            v_confidence = verification.get("confidence", 5) / 10.0
            confidence = (confidence + v_confidence) / 2

        return SolverResult(
            answer_index=final_state.get("answer_index", 0),
            confidence=confidence,
            reasoning=final_state.get("reasoning", ""),
            references=final_state.get("rag_references", []),
            llm_calls=final_state.get("llm_calls_count", 0),
            model_used="solver-graph-v2",
            option_scores=option_scores,
            verification=verification,
        )
    except Exception as e:
        logger.error(f"Solver failed: {e}", exc_info=True)
        return SolverResult(
            answer_index=0,
            confidence=0.1,
            reasoning=f"Error: {str(e)}",
            references=[],
            llm_calls=0,
            model_used="solver-graph-v2-error",
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
