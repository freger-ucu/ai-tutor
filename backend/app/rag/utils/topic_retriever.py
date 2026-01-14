"""
Topic-based retriever for Agentic RAG.

Two-stage retrieval:
1. Find relevant TOC topics using semantic search on topic_embedding
2. Get textbook pages for matched topics using book_topic_id

This approach is especially effective for Ukrainian language questions
where RAG needs to find the correct grammatical concept/rule.
"""

import logging
import numpy as np
from typing import List, Dict, Tuple, Optional

from .rag_data_loader import get_data_loader
from .llm_client import get_llm_client

logger = logging.getLogger(__name__)


class TopicRetriever:
    """
    Two-stage retrieval: Topics → Pages.

    Uses pre-computed topic_embedding from TOC for semantic search,
    then retrieves exact pages by book_topic_id.
    """

    def __init__(self):
        self.data_loader = get_data_loader()
        self.llm_client = get_llm_client()

    async def find_relevant_topics(
        self,
        question: str,
        subject: str,
        grade: int,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Stage 1: Find relevant TOC topics using semantic search.

        Args:
            question: Question text to match
            subject: Subject name for filtering
            grade: Grade for filtering
            top_k: Number of topics to return

        Returns:
            List of topic dicts with scores, sorted by relevance
        """
        # Get TOC for subject/grade
        toc = self.data_loader.get_topics_for_subject_grade(subject, grade)

        if len(toc) == 0:
            logger.debug(f" No topics found for {subject}, grade {grade}")
            return []

        # Get question embedding (API call, not LLM!)
        query_embedding = await self.llm_client.embed(question)
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Get topic embeddings
        topic_embeddings_list = []
        valid_indices = []

        for i, (idx, row) in enumerate(toc.iterrows()):
            emb = row.get('topic_embedding')
            if emb is not None:
                if isinstance(emb, np.ndarray):
                    topic_embeddings_list.append(emb)
                else:
                    topic_embeddings_list.append(np.array(emb))
                valid_indices.append(i)

        if not topic_embeddings_list:
            logger.debug(f" No topic embeddings available")
            return []

        topic_embeddings = np.vstack(topic_embeddings_list).astype(np.float32)

        # Normalize embeddings
        norms = np.linalg.norm(topic_embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        topic_embeddings = topic_embeddings / norms

        # Cosine similarity
        similarities = np.dot(topic_embeddings, query_vec)

        # Get top-k topics
        top_local_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for local_idx in top_local_indices:
            original_idx = valid_indices[local_idx]
            row = toc.iloc[original_idx]

            # Extract subtopics safely
            subtopics = row.get("subtopics", [])
            if subtopics is None:
                subtopics = []
            elif isinstance(subtopics, np.ndarray):
                subtopics = subtopics.tolist()

            results.append({
                "topic_title": str(row.get("topic_title", "")),
                "section_title": str(row.get("section_title", "")),
                "score": float(similarities[local_idx]),
                "book_topic_id": str(row.get("book_topic_id", "")),
                "subtopics": subtopics,
                "topic_start_page": row.get("topic_start_page"),
                "topic_end_page": row.get("topic_end_page"),
                "topic_summary": str(row.get("topic_summary", ""))[:500],  # Truncate
            })

        logger.debug(f" Found {len(results)} topics, top: {results[0]['topic_title'][:50] if results else 'none'}")

        return results

    async def get_pages_for_topics(
        self,
        topics: List[Dict],
        subject: str,
        grade: int,
        max_pages: int = 4
    ) -> List[Dict]:
        """
        Stage 2: Get textbook pages for matched topics.

        Uses book_topic_id to find exact pages belonging to each topic.

        Args:
            topics: List of matched topics from stage 1
            subject: Subject name
            grade: Grade
            max_pages: Maximum total pages to return

        Returns:
            List of page dicts with content and metadata
        """
        pages = self.data_loader.get_pages_for_subject_grade(subject, grade)

        if len(pages) == 0:
            logger.debug(f" No pages found for {subject}, grade {grade}")
            return []

        collected_pages = []
        pages_per_topic = max(1, max_pages // len(topics)) if topics else max_pages

        for topic in topics:
            topic_id = topic.get("book_topic_id")
            topic_title = topic.get("topic_title", "")

            # Try to find pages by topic_id
            if topic_id and "book_topic_id" in pages.columns:
                topic_pages = pages[pages["book_topic_id"] == topic_id]
            else:
                topic_pages = pages.iloc[0:0]  # Empty DataFrame

            # Fallback: search by topic_title if no pages found
            if len(topic_pages) == 0 and topic_title:
                topic_pages = pages[
                    pages["topic_title"].fillna("").str.contains(
                        topic_title, na=False, regex=False, case=False
                    )
                ]

            # Add pages with topic context
            for _, page_row in topic_pages.head(pages_per_topic).iterrows():
                collected_pages.append({
                    "page_text": str(page_row.get("page_text", "")),
                    "topic_title": topic_title,
                    "section_title": topic.get("section_title", ""),
                    "page_number": int(page_row.get("book_page_number", 0)),
                    "book_name": str(page_row.get("book_name", "")),
                    "book_topic_id": topic_id,
                    "matched_topic_score": topic.get("score", 0),
                    "subtopics": topic.get("subtopics", []),
                })

        logger.debug(f" Retrieved {len(collected_pages)} pages for {len(topics)} topics")

        return collected_pages[:max_pages]

    async def retrieve(
        self,
        question: str,
        subject: str,
        grade: int,
        top_k_topics: int = 3,
        max_pages: int = 4
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Full two-stage retrieval.

        Args:
            question: Question text
            subject: Subject name
            grade: Grade
            top_k_topics: Number of topics to match
            max_pages: Maximum pages to retrieve

        Returns:
            Tuple of (matched_topics, pages)
        """
        # Stage 1: Find relevant topics
        topics = await self.find_relevant_topics(
            question, subject, grade, top_k_topics
        )

        if not topics:
            return [], []

        # Stage 2: Get pages for matched topics
        pages = await self.get_pages_for_topics(
            topics, subject, grade, max_pages
        )

        return topics, pages


def format_context_with_topics(
    pages: List[Dict],
    topics: List[Dict],
    max_chars: int = 4000
) -> Tuple[str, List[Dict]]:
    """
    Format retrieved pages into context string with topic information.

    For math content: Uses full page content (no truncation) to preserve worked examples.

    Args:
        pages: List of page dicts
        topics: List of matched topic dicts
        max_chars: Maximum context length

    Returns:
        Tuple of (formatted context string, list of references)
    """
    # Detect if this is math content
    is_math = any(
        "алгебра" in str(t.get("topic_title", "")).lower()
        or "геометр" in str(t.get("topic_title", "")).lower()
        for t in topics
    )

    # Build topics summary
    topics_summary = []
    for i, topic in enumerate(topics, 1):
        subtopics_str = ", ".join(topic.get("subtopics", [])[:5])
        topics_summary.append(
            f"{i}. {topic['topic_title']} (score: {topic['score']:.2f})\n"
            f"   Підтеми: {subtopics_str}"
        )

    topics_section = "### ЗНАЙДЕНІ ТЕМИ:\n" + "\n".join(topics_summary)

    # Build pages section
    context_parts = [topics_section, "\n### КОНТЕКСТ З ПІДРУЧНИКА:\n"]
    references = []
    total_chars = len(topics_section) + 50

    # Different strategy for math vs other subjects
    if is_math:
        # Math: Max 3 pages, FULL content each
        max_pages_to_include = min(len(pages), 3)
    else:
        # Standard: all pages with truncation
        max_pages_to_include = len(pages)
        chars_per_page = (max_chars - total_chars) // max(len(pages), 1)

    for i, page in enumerate(pages[:max_pages_to_include], 1):
        page_text = page.get("page_text", "")

        # Only truncate for non-math content
        if not is_math and len(page_text) > chars_per_page:
            page_text = page_text[:chars_per_page] + "..."

        topic_title = page.get("topic_title", "")
        page_num = page.get("page_number", 0)
        book_name = page.get("book_name", "")

        context_part = f"""
[Джерело {i}]
- Тема: {topic_title}
- Сторінка: {page_num}
- Підручник: {book_name}

{page_text}
---"""

        # For non-math, still check max_chars
        if not is_math and total_chars + len(context_part) > max_chars:
            break

        context_parts.append(context_part)
        total_chars += len(context_part)

        references.append({
            "source_id": i,
            "topic": topic_title,
            "page": page_num,
            "book": book_name,
        })

    return "\n".join(context_parts), references


# Global instance
_topic_retriever: Optional[TopicRetriever] = None


def get_topic_retriever() -> TopicRetriever:
    """Get singleton topic retriever instance."""
    global _topic_retriever
    if _topic_retriever is None:
        _topic_retriever = TopicRetriever()
    return _topic_retriever
