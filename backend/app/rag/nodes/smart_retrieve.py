"""
Smart Retrieve Node - Zero-LLM retrieval using hybrid search.

This node performs retrieval WITHOUT any LLM calls:
- Uses pre-computed embeddings from parquet files
- BM25 + Vector search + RRF fusion
- Subject/Grade filtering

For Ukrainian language: Uses topic-based retrieval via TOC embeddings.

V6 Changes:
- Cross-Encoder reranking for better precision
- Option-aware retrieval for Ukrainian language
"""

from typing import Dict, Any, List

from ..state import AgenticRAGState
from ..config import get_settings
from ..utils.hybrid_retriever import get_retriever, format_context
from ..utils.reranker import get_reranker, CROSS_ENCODER_AVAILABLE
from ..utils.passage_extractor import (
    get_passage_extractor,
    format_context_with_passages,
    PassageConfig,
)


async def smart_retrieve_node(state: AgenticRAGState) -> Dict[str, Any]:
    """
    Smart retrieval node - zero LLM calls.

    For Ukrainian language: Uses topic-based retrieval (TOC → Pages)
    For other subjects: Uses hybrid search (BM25 + Vector + RRF)

    V6: Now with Cross-Encoder reranking and option-aware retrieval.
    """
    question_text = state["question_text"]
    subject = state["subject"]
    grade = state["grade"]
    answers = state.get("answers", [])  # Answer options for option-aware retrieval
    settings = get_settings()

    # Use enhanced retrieval for Ukrainian language
    if subject == "Українська мова":
        return await _retrieve_ukrainian(
            question_text=question_text,
            subject=subject,
            grade=grade,
            answers=answers,
            max_chars=settings.retrieval_max_chars,
        )

    # Standard hybrid retrieval for other subjects
    retriever = get_retriever()
    docs = await retriever.retrieve(
        query=question_text,
        subject=subject,
        grade=grade,
    )

    # Calculate average retrieval score
    avg_score = sum(d["rrf_score"] for d in docs) / len(docs) if docs else 0.0

    # Format context for prompt
    context_text, references = format_context(
        docs,
        max_chars=settings.retrieval_max_chars,
        subject=subject
    )

    return {
        "retrieved_docs": docs,
        "matched_topics": [],
        "retrieval_score": avg_score,
        "context_text": context_text,
        "references": references,
    }


async def _retrieve_ukrainian(
    question_text: str,
    subject: str,
    grade: int,
    answers: List[str] = None,
    max_chars: int = 6000,
) -> Dict[str, Any]:
    """
    Enhanced retrieval for Ukrainian language with passage-level extraction.

    V8 Pipeline:
    1. Hybrid retrieval (BM25 with lemmatization + Vector + RRF) - get 40 candidates
    2. Topic matching for boosting
    3. Cross-Encoder reranking with option-awareness → top 10
    4. [NEW] Passage extraction: split into paragraphs, BM25 rank
    5. Return focused passages instead of full pages

    This reduces noise and helps LLM focus on specific grammar rules.
    """
    from ..utils.topic_retriever import (
        get_topic_retriever,
        format_context_with_topics
    )
    from ..config import get_subject_config
    import asyncio

    if answers is None:
        answers = []

    # Get subject-specific config
    subject_config = get_subject_config(subject)
    retrieval_top_k = subject_config.retrieval_top_k or 30
    context_max_chars = subject_config.max_context_chars or max_chars
    use_passage_extraction = getattr(subject_config, 'use_passage_extraction', False)

    hybrid_retriever = get_retriever()
    topic_retriever = get_topic_retriever()
    reranker = get_reranker()

    # Stage 1: Run Hybrid + Topic retrieval in parallel
    hybrid_task = hybrid_retriever.retrieve(
        query=question_text,
        subject=subject,
        grade=grade,
        top_k=retrieval_top_k,  # V7: Use config-based top_k (40 for Ukrainian)
    )
    topic_task = topic_retriever.find_relevant_topics(
        question=question_text,
        subject=subject,
        grade=grade,
        top_k=10,
    )

    hybrid_docs, topics = await asyncio.gather(hybrid_task, topic_task)

    # Stage 2: Topic boosting (pre-reranking)
    matched_topic_ids = set()
    for topic in topics:
        if topic.get("score", 0) >= 0.4:
            matched_topic_ids.add(topic.get("book_topic_id", ""))

    for doc in hybrid_docs:
        doc_topic_id = doc.get("book_topic_id", "")
        if doc_topic_id in matched_topic_ids:
            doc["topic_boosted"] = True
        else:
            doc["topic_boosted"] = False

    # Stage 3: Cross-Encoder Reranking with option-awareness
    # Convert answers to list if numpy array
    answers_list = list(answers) if hasattr(answers, '__len__') and len(answers) > 0 else []

    # V7: Increase final docs from 8 to 10 for better coverage
    final_docs_count = 10

    if CROSS_ENCODER_AVAILABLE and len(hybrid_docs) > 0:
        if len(answers_list) > 0:
            # Option-aware reranking: considers question + each answer option
            final_docs = reranker.rerank_with_options(
                question=question_text,
                options=answers_list,
                docs=hybrid_docs,
                top_k=final_docs_count,
                max_length=512,
            )
            rerank_method = "option-aware"
        else:
            # Standard reranking
            final_docs = reranker.rerank(
                query=question_text,
                docs=hybrid_docs,
                top_k=final_docs_count,
                max_length=512,
            )
            rerank_method = "standard"
    else:
        # Fallback: sort by RRF score
        hybrid_docs.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        final_docs = hybrid_docs[:final_docs_count]
        rerank_method = "rrf-only"

    # Stage 4: Passage-level extraction (V8)
    if use_passage_extraction and final_docs:
        passage_extractor = get_passage_extractor()

        # Build config from subject settings
        passage_config = PassageConfig(
            top_k_passages=getattr(subject_config, 'passage_top_k', 5),
            max_pages_for_passages=getattr(subject_config, 'passage_max_pages', 3),
            pages_to_process=8,
            min_paragraph_length=getattr(subject_config, 'passage_min_length', 50),
            max_paragraph_length=getattr(subject_config, 'passage_max_length', 800),
            max_context_chars=context_max_chars,
            include_best_option=True,
        )

        passages, extraction_metadata = passage_extractor.extract_passages(
            reranked_docs=final_docs,
            question=question_text,
            answers=answers_list,
            config=passage_config,
        )

        # Format context with passages
        context_text, references = format_context_with_passages(
            passages=passages,
            topics=topics,
            max_chars=context_max_chars,
        )

        # Calculate average score from passages
        if passages:
            avg_score = sum(p.bm25_score for p in passages) / len(passages)
        else:
            avg_score = 0.0

        print(f"  [SmartRetrieve] Ukrainian V8: {len(passages)} passages from {extraction_metadata.get('pages_processed', 0)} pages ({rerank_method})")

    else:
        # Fallback: original format_context_with_topics
        context_text, references = format_context_with_topics(
            final_docs, topics, max_chars=context_max_chars
        )

        # Calculate average score
        if final_docs:
            if "rerank_score" in final_docs[0]:
                avg_score = sum(d.get("rerank_score", 0) for d in final_docs) / len(final_docs)
            else:
                avg_score = sum(d.get("rrf_score", 0) for d in final_docs) / len(final_docs)
        else:
            avg_score = 0.0

        topic_boosted_count = sum(1 for d in final_docs if d.get("topic_boosted", False))
        print(f"  [SmartRetrieve] Ukrainian: {len(final_docs)} docs ({topic_boosted_count} topic-boosted, {rerank_method}, top_k={retrieval_top_k})")

    return {
        "retrieved_docs": final_docs,
        "matched_topics": topics,
        "retrieval_score": avg_score,
        "context_text": context_text,
        "references": references,
    }


def _merge_pages(topic_pages: list, hybrid_docs: list, max_total: int = 6) -> list:
    """Merge topic-based and hybrid results, avoiding duplicates."""
    merged = topic_pages[:4]
    seen_texts = {p.get("page_text", "")[:100] for p in merged}

    for doc in hybrid_docs:
        if len(merged) >= max_total:
            break
        text_preview = doc.get("page_text", "")[:100]
        if text_preview not in seen_texts:
            merged.append(doc)
            seen_texts.add(text_preview)

    return merged
