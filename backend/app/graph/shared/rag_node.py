"""
Configurable RAG retrieval node factory.

Creates RAG nodes with different configurations for different flows:
- Notes flow: Parallel queries (topic + prerequisites)
- Solver flow: Single query with topic hints
- Test gen flow: Topic-focused retrieval for context
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional, Tuple

from app.services.tracing import trace_retriever
from app.rag.utils.hybrid_retriever import get_retriever, format_context
from app.rag.utils.topic_retriever import (
    get_topic_retriever,
    format_context_with_topics,
)

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG retrieval node."""

    max_chars: int = 6000
    top_k: int = 4
    include_references: bool = True
    parallel_queries: bool = False
    use_topic_retriever: bool = False
    top_k_topics: int = 3


def create_rag_node(
    config: RAGConfig = RAGConfig(),
    query_key: str = "query",
    subject_key: str = "subject",
    grade_key: str = "grade",
    prereq_key: str = "prereq_queries",
    context_output_key: str = "rag_context",
    references_output_key: str = "rag_references",
    docs_output_key: str = "retrieved_docs",
) -> Callable:
    """
    Factory function to create RAG retrieval node with config.

    Args:
        config: RAG configuration
        query_key: State key for main query
        subject_key: State key for subject
        grade_key: State key for grade
        prereq_key: State key for prerequisite queries (if parallel)
        context_output_key: State key for formatted context output
        references_output_key: State key for references output
        docs_output_key: State key for raw docs output

    Returns:
        Async node function compatible with LangGraph
    """

    @trace_retriever(name="rag_retrieve")
    async def rag_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve context from RAG system.

        Supports three modes:
        1. Standard: Single query retrieval
        2. Parallel: Main query + prerequisite queries
        3. Topic-based: Use TopicRetriever for better topic matching
        """
        query = state.get(query_key, "")
        subject = state.get(subject_key, "")
        grade = state.get(grade_key, 9)

        if not query:
            logger.warning("Empty query provided to RAG node")
            return {
                context_output_key: "",
                references_output_key: [],
                docs_output_key: [],
            }

        retriever = get_retriever()

        # Mode 1: Topic-based retrieval (for Ukrainian/specific cases)
        if config.use_topic_retriever:
            topic_retriever = get_topic_retriever()
            matched_topics, pages = await topic_retriever.retrieve(
                question=query,
                subject=subject,
                grade=grade,
                top_k_topics=config.top_k_topics,
                max_pages=config.top_k,
            )
            context, references = format_context_with_topics(
                pages, matched_topics, max_chars=config.max_chars
            )
            return {
                context_output_key: context,
                references_output_key: references if config.include_references else [],
                docs_output_key: pages,
                "matched_topics": matched_topics,
            }

        # Mode 2: Parallel queries (for notes with prerequisites)
        if config.parallel_queries and prereq_key in state:
            prereq_queries = state.get(prereq_key, [])
            if prereq_queries:
                # Run main + prereq queries in parallel
                main_task = retriever.retrieve(
                    query=query, subject=subject, grade=grade, top_k=config.top_k
                )
                prereq_tasks = [
                    retriever.retrieve(
                        query=pq, subject=subject, grade=grade, top_k=2
                    )
                    for pq in prereq_queries[:3]  # Limit prereqs
                ]

                results = await asyncio.gather(main_task, *prereq_tasks)
                main_docs = results[0]
                prereq_docs = [doc for docs in results[1:] for doc in docs]

                # Format main context
                main_context, main_refs = format_context(
                    main_docs, max_chars=config.max_chars // 2, subject=subject
                )

                # Format prereq context (if any)
                prereq_context = ""
                prereq_refs = []
                if prereq_docs:
                    prereq_context, prereq_refs = format_context(
                        prereq_docs, max_chars=config.max_chars // 2, subject=subject
                    )

                return {
                    context_output_key: main_context,
                    references_output_key: main_refs + prereq_refs if config.include_references else [],
                    docs_output_key: main_docs + prereq_docs,
                    "prereq_context": prereq_context,
                }

        # Mode 3: Standard single query
        docs = await retriever.retrieve(
            query=query, subject=subject, grade=grade, top_k=config.top_k
        )
        context, references = format_context(
            docs, max_chars=config.max_chars, subject=subject
        )

        return {
            context_output_key: context,
            references_output_key: references if config.include_references else [],
            docs_output_key: docs,
        }

    return rag_retrieve_node


# Pre-configured nodes for common use cases
def create_notes_rag_node() -> Callable:
    """RAG node configured for notes generation with parallel prereq retrieval."""
    return create_rag_node(
        config=RAGConfig(
            max_chars=8000,
            top_k=5,
            parallel_queries=True,
            include_references=True,
        ),
        query_key="topic_definition",
    )


def create_solver_rag_node() -> Callable:
    """RAG node configured for question solving."""
    return create_rag_node(
        config=RAGConfig(
            max_chars=6000,
            top_k=4,
            include_references=True,
        ),
        query_key="question_text",
    )


def create_test_gen_rag_node() -> Callable:
    """RAG node configured for test generation context."""
    return create_rag_node(
        config=RAGConfig(
            max_chars=6000,
            top_k=4,
            include_references=False,
        ),
        query_key="topic_definition",
    )
