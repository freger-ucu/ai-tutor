"""
Hybrid Retriever for Agentic RAG - BM25 + Vector search + RRF fusion.

Zero-LLM retrieval using pre-computed embeddings.

V7 Changes:
- Ukrainian lemmatization with pymorphy2 for better BM25 matching

V9 Changes:
- Dual-Field BM25: separate surface and lemma indices for Ukrainian
- Configurable RRF weights per subject (BM25 vs Vector)
"""

import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)

# BM25 dependency
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None

# Ukrainian morphology dependency (lazy initialization)
MORPH_ANALYZER = None
PYMORPHY_AVAILABLE = False

def _get_morph_analyzer():
    """Lazy initialization of morphology analyzer."""
    global MORPH_ANALYZER, PYMORPHY_AVAILABLE
    if MORPH_ANALYZER is None:
        try:
            import pymorphy2
            MORPH_ANALYZER = pymorphy2.MorphAnalyzer(lang='uk')
            PYMORPHY_AVAILABLE = True
        except Exception as e:
            # pymorphy2 may have compatibility issues with newer Python
            logger.warning(f"pymorphy2 not available: {e}")
            MORPH_ANALYZER = None
            PYMORPHY_AVAILABLE = False
    return MORPH_ANALYZER

from ..config import get_settings, get_subject_config
from .llm_client import get_llm_client
from .rag_data_loader import get_data_loader


class HybridRetriever:
    """
    Hybrid retrieval: BM25 keyword search + vector semantic search + RRF fusion.

    Features:
    - Zero LLM calls for retrieval (uses pre-computed embeddings)
    - TOC-based topic matching for intelligent filtering
    - Subject/grade filtering
    - RRF fusion for combining results
    """

    def __init__(self):
        self.data_loader = get_data_loader()
        self.llm_client = get_llm_client()
        self.settings = get_settings()

        # Cache for BM25 indices
        self._bm25_cache: Dict[str, BM25Okapi] = {}
        self._tokenized_cache: Dict[str, Tuple[List, List]] = {}

        # V9: Dual-field BM25 caches for Ukrainian
        self._bm25_surface_cache: Dict[str, BM25Okapi] = {}
        self._bm25_lemma_cache: Dict[str, BM25Okapi] = {}
        self._dual_field_page_indices: Dict[str, List[int]] = {}

    async def retrieve(
        self,
        query: str,
        subject: str,
        grade: int,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant textbook pages for a query.

        V9: Uses dual-field BM25 and configurable RRF weights for Ukrainian.

        Args:
            query: Search query (question text)
            subject: Subject name for filtering
            grade: Grade for filtering
            top_k: Number of results (default from config with subject boost)

        Returns:
            List of dicts with page info and RRF scores
        """
        subject_config = get_subject_config(subject)

        if top_k is None:
            top_k = int(self.settings.retrieval_top_k * subject_config.retrieval_boost)

        # Get candidate pages
        candidates = self.data_loader.get_pages_for_subject_grade(subject, grade)

        if len(candidates) == 0:
            logger.warning(f"No pages found for {subject}, grade {grade}")
            return []

        # V9: Use dual-field BM25 for Ukrainian if enabled
        if subject_config.use_dual_field_bm25:
            bm25_results = self._bm25_search_dual_field(
                query, candidates, top_k * 2,
                alpha=subject_config.bm25_surface_weight
            )
        else:
            # Standard BM25 search (subject-aware tokenization)
            bm25_results = self._bm25_search(query, candidates, top_k * 2, subject=subject)

        # Vector search
        vector_results = await self._vector_search(query, candidates, top_k * 2)

        # V9: RRF fusion with configurable weights
        fused = self._rrf_fusion(
            bm25_results, vector_results, candidates,
            bm25_weight=subject_config.rrf_bm25_weight,
            vector_weight=subject_config.rrf_vector_weight
        )

        return fused[:top_k]

    async def retrieve_with_topic_hint(
        self,
        query: str,
        subject: str,
        grade: int,
        retry_hint: str,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        """
        Retrieve with a retry hint - combines original query with hint.

        Args:
            query: Original question text
            subject: Subject name
            grade: Grade
            retry_hint: Hint for better retrieval (from agent decision)
            top_k: Number of results

        Returns:
            List of dicts with page info
        """
        # Combine query with hint for better matching
        enhanced_query = f"{query} {retry_hint}"
        return await self.retrieve(enhanced_query, subject, grade, top_k)

    def _bm25_search(
        self,
        query: str,
        candidates: pd.DataFrame,
        top_k: int,
        subject: str = ""
    ) -> List[Tuple[int, float]]:
        """BM25 keyword search with subject-aware tokenization."""
        if not BM25_AVAILABLE:
            return []

        # Cache key includes subject for different tokenization strategies
        cache_key = f"{candidates['global_discipline_name'].iloc[0]}_{candidates['grade'].iloc[0]}_{subject}"

        # Build or get BM25 index
        if cache_key not in self._bm25_cache:
            page_indices = candidates.index.tolist()
            tokenized_docs = []

            for idx in page_indices:
                text = str(candidates.loc[idx, 'page_text'])
                tokens = self._tokenize_ukrainian(text, subject=subject)
                tokenized_docs.append(tokens)

            self._bm25_cache[cache_key] = BM25Okapi(tokenized_docs)
            self._tokenized_cache[cache_key] = (page_indices, tokenized_docs)
        else:
            page_indices = self._tokenized_cache[cache_key][0]

        bm25 = self._bm25_cache[cache_key]
        query_tokens = self._tokenize_ukrainian(query, subject=subject)
        scores = bm25.get_scores(query_tokens)

        # Get top results
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = [
            (page_indices[i], float(scores[i]))
            for i in top_indices
            if scores[i] > 0
        ]

        return results

    def _bm25_search_dual_field(
        self,
        query: str,
        candidates: pd.DataFrame,
        top_k: int,
        alpha: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        V9: Dual-field BM25 search with separate surface and lemma indices.

        This approach builds two separate BM25 indices:
        - Surface index: original word forms (lowercase, no stopwords)
        - Lemma index: lemmatized forms via pymorphy2

        Final score = alpha * BM25(surface) + (1-alpha) * BM25(lemma)

        This helps when pymorphy2 makes lemmatization errors - surface form rescues.

        Args:
            query: Search query
            candidates: DataFrame with pages
            top_k: Number of results
            alpha: Weight for surface tokens (default 0.5 = equal weight)

        Returns:
            List of (page_id, combined_score) tuples
        """
        if not BM25_AVAILABLE:
            return []

        cache_key = f"{candidates['global_discipline_name'].iloc[0]}_{candidates['grade'].iloc[0]}_dual"

        # Build or get dual-field indices
        if cache_key not in self._bm25_surface_cache:
            page_indices = candidates.index.tolist()
            surface_docs = []
            lemma_docs = []

            for idx in page_indices:
                text = str(candidates.loc[idx, 'page_text'])
                surface_tokens, lemma_tokens = self._tokenize_dual_field(text)
                surface_docs.append(surface_tokens)
                lemma_docs.append(lemma_tokens)

            self._bm25_surface_cache[cache_key] = BM25Okapi(surface_docs)
            self._bm25_lemma_cache[cache_key] = BM25Okapi(lemma_docs)
            self._dual_field_page_indices[cache_key] = page_indices

        page_indices = self._dual_field_page_indices[cache_key]
        bm25_surface = self._bm25_surface_cache[cache_key]
        bm25_lemma = self._bm25_lemma_cache[cache_key]

        # Tokenize query into both forms
        query_surface, query_lemma = self._tokenize_dual_field(query)

        # Get scores from both indices
        surface_scores = bm25_surface.get_scores(query_surface)
        lemma_scores = bm25_lemma.get_scores(query_lemma)

        # V9.1 FIX: Use rank-based fusion instead of score normalization
        # Score normalization caused ranking issues - use RRF-style rank fusion
        surface_ranks = np.argsort(np.argsort(-surface_scores))  # Rank 0 = best
        lemma_ranks = np.argsort(np.argsort(-lemma_scores))

        # RRF-style combination: lower rank = better
        k = 60  # RRF constant
        combined_scores = (
            alpha / (k + surface_ranks + 1) +
            (1 - alpha) / (k + lemma_ranks + 1)
        )

        # Get top results
        top_indices = np.argsort(combined_scores)[::-1][:top_k]

        results = [
            (page_indices[i], float(combined_scores[i]))
            for i in top_indices
            if combined_scores[i] > 0
        ]

        return results

    @staticmethod
    def _tokenize_dual_field(text: str) -> Tuple[List[str], List[str]]:
        """
        V9: Tokenize text into separate surface and lemma token lists.

        IMPORTANT for Ukrainian grammar:
        - Keep "не", "ні", "що", "як", "та", "а", "й", "чи" - critical for grammar!
        - These words determine sentence types (impersonal, generalized, etc.)

        Returns:
            Tuple of (surface_tokens, lemma_tokens)
        """
        if not isinstance(text, str):
            return [], []

        # Minimal stopwords - preserve grammatically important words!
        stopwords = {
            'і', 'в', 'на', 'з', 'за', 'до', 'для', 'про', 'при',
            'це', 'він', 'вона', 'воно', 'вони', 'ми', 'ви',
            'його', 'її', 'їх', 'цей', 'цього', 'після', 'під', 'над',
        }

        text = text.lower()

        # Replace punctuation with spaces
        for char in '.,;:!?()[]{}«»"\'-/\\':
            text = text.replace(char, ' ')

        raw_tokens = text.split()

        # Surface tokens: filter by length and stopwords
        surface_tokens = [t for t in raw_tokens if len(t) >= 1 and t not in stopwords]

        # Lemma tokens: apply pymorphy2 lemmatization
        lemma_tokens = []
        morph = _get_morph_analyzer()

        if morph is not None:
            for token in surface_tokens:
                try:
                    parsed = morph.parse(token)
                    if parsed:
                        lemma = parsed[0].normal_form
                        if lemma not in stopwords:
                            lemma_tokens.append(lemma)
                        else:
                            lemma_tokens.append(token)  # Keep original if lemma is stopword
                    else:
                        lemma_tokens.append(token)
                except Exception:
                    lemma_tokens.append(token)  # Fallback to surface form
        else:
            # No pymorphy2 - use surface tokens as lemmas
            lemma_tokens = surface_tokens.copy()

        return surface_tokens, lemma_tokens

    async def _vector_search(
        self,
        query: str,
        candidates: pd.DataFrame,
        top_k: int
    ) -> List[Tuple[int, float]]:
        """Vector semantic search using embeddings."""
        # Get query embedding (API call, not LLM!)
        query_embedding = await self.llm_client.embed(query)
        query_vec = np.array(query_embedding, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Get page embeddings
        page_indices = candidates.index.tolist()
        embeddings_list = []

        for idx in page_indices:
            emb = candidates.loc[idx, 'page_text_embedding']
            if isinstance(emb, np.ndarray):
                embeddings_list.append(emb)
            else:
                embeddings_list.append(np.array(emb))

        page_embeddings = np.vstack(embeddings_list).astype(np.float32)

        # Normalize
        norms = np.linalg.norm(page_embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        page_embeddings = page_embeddings / norms

        # Cosine similarities
        similarities = np.dot(page_embeddings, query_vec)

        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = [
            (page_indices[i], float(similarities[i]))
            for i in top_indices
        ]

        return results

    def _rrf_fusion(
        self,
        bm25_results: List[Tuple[int, float]],
        vector_results: List[Tuple[int, float]],
        candidates: pd.DataFrame,
        bm25_weight: float = 1.0,
        vector_weight: float = 1.0,
    ) -> List[Dict]:
        """
        Reciprocal Rank Fusion to combine results.

        V9: Added configurable weights for BM25 and Vector contributions.
        For Ukrainian grammar, BM25 is more important (exact term matching).

        Args:
            bm25_results: BM25 search results
            vector_results: Vector search results
            candidates: DataFrame with page data
            bm25_weight: Weight for BM25 contribution (default 1.0)
            vector_weight: Weight for Vector contribution (default 1.0)
        """
        k = self.settings.rrf_k

        # Rank mappings
        bm25_ranks = {page_id: rank for rank, (page_id, _) in enumerate(bm25_results)}
        vector_ranks = {page_id: rank for rank, (page_id, _) in enumerate(vector_results)}

        # All unique page IDs
        all_page_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())

        # Calculate RRF scores with weights
        rrf_scores = []
        for page_id in all_page_ids:
            score = 0.0

            if page_id in bm25_ranks:
                score += bm25_weight * (1.0 / (k + bm25_ranks[page_id] + 1))

            if page_id in vector_ranks:
                score += vector_weight * (1.0 / (k + vector_ranks[page_id] + 1))

            try:
                page_row = candidates.loc[page_id]
                rrf_scores.append({
                    "page_id": int(page_id),
                    "rrf_score": float(score),
                    "page_text": str(page_row.get("page_text", "")),
                    "topic_title": str(page_row.get("topic_title", "")),
                    "section_title": str(page_row.get("section_title", "")),
                    "page_number": int(page_row.get("book_page_number", 0)),
                    "book_name": str(page_row.get("book_name", "")),
                    "book_topic_id": str(page_row.get("book_topic_id", "")),
                })
            except KeyError:
                continue

        # Sort by RRF score
        rrf_scores.sort(key=lambda x: x["rrf_score"], reverse=True)

        return rrf_scores

    @staticmethod
    def _tokenize_ukrainian(text: str, subject: str = "", use_lemmatization: bool = True) -> List[str]:
        """
        Ukrainian tokenizer with subject-aware stopwords and optional lemmatization.

        V7: Added pymorphy2 lemmatization for better BM25 matching.
        - Keeps both surface form AND lemma for each token
        - This allows matching "речення" with "речень", "реченням", etc.

        For Ukrainian language grammar questions:
        - Keep critical grammar tokens: "не", "та", "й", "а", "бо", "чи"
        - Keep subordinate conjunctions: "що", "як", "коли", "якщо", "щоб"
        - These determine sentence types (impersonal, generalized, etc.)

        For other subjects: standard stopword filtering.
        """
        if not isinstance(text, str):
            return []

        # Subject-aware stopwords
        if subject == "Українська мова":
            # MINIMAL stopwords for grammar - preserve grammatically important words!
            # "що", "як", "бо", "чи" - визначають тип речення
            # "не", "та", "й", "а" - критичні для граматичного аналізу
            stopwords = {
                'і', 'в', 'на', 'з', 'за', 'до', 'для', 'про', 'при',
                'це', 'він', 'вона', 'воно', 'вони', 'ми', 'ви',
                'його', 'її', 'їх', 'цей', 'цього', 'після', 'під', 'над',
            }
            min_token_len = 1  # Keep short tokens like "не", "та", "й", "а"
        else:
            # Standard stopwords for other subjects
            stopwords = {
                'і', 'в', 'на', 'з', 'за', 'до', 'що', 'як', 'не', 'та',
                'це', 'для', 'про', 'при', 'але', 'чи', 'або', 'ні',
                'так', 'він', 'вона', 'воно', 'вони', 'ми', 'ви', 'ця',
                'той', 'ті', 'яка', 'який', 'яке', 'які', 'його', 'її',
                'їх', 'цей', 'цього', 'цій', 'цим', 'після', 'під', 'над',
            }
            min_token_len = 2

        text = text.lower()

        # Replace punctuation
        for char in '.,;:!?()[]{}«»"\'-/\\':
            text = text.replace(char, ' ')

        raw_tokens = text.split()
        tokens = [t for t in raw_tokens if len(t) >= min_token_len and t not in stopwords]

        # Apply lemmatization for Ukrainian language subject
        if use_lemmatization and subject == "Українська мова":
            morph = _get_morph_analyzer()
            if morph is not None:
                result = []
                for token in tokens:
                    result.append(token)  # Keep surface form
                    # Add lemma if different
                    try:
                        parsed = morph.parse(token)
                        if parsed:
                            lemma = parsed[0].normal_form
                            if lemma != token and lemma not in stopwords:
                                result.append(lemma)
                    except Exception:
                        pass  # Skip on error
                return result

        return tokens


def format_context(
    docs: List[Dict],
    max_chars: int = 6000,
    subject: str = "",
) -> Tuple[str, List[Dict]]:
    """
    Format retrieved documents into context string for prompt.

    For Algebra: Uses full page content (no truncation) to preserve worked examples.

    Args:
        docs: Retrieved document dicts
        max_chars: Maximum total characters
        subject: Subject name

    Returns:
        Tuple of (formatted context string, list of references)
    """
    # Detect if this is Algebra content
    is_algebra = (
        "алгебра" in subject.lower()
        or any("алгебра" in str(d.get("topic_title", "")).lower()
               or "геометр" in str(d.get("topic_title", "")).lower()
               for d in docs)
    )

    context_parts = []
    references = []
    total_chars = 0

    # Different strategy for Algebra vs other subjects
    if is_algebra:
        # Algebra: Max 3 docs, FULL content each
        max_docs_to_include = min(len(docs), 3)
    else:
        # Standard: all docs with truncation
        max_docs_to_include = len(docs)
        chars_per_doc = max_chars // max(len(docs), 1)

    for i, doc in enumerate(docs[:max_docs_to_include], 1):
        page_text = doc.get("page_text", "")

        # Only truncate for non-Algebra content
        if not is_algebra and len(page_text) > chars_per_doc:
            page_text = page_text[:chars_per_doc] + "..."

        topic = doc.get("topic_title", "")
        section = doc.get("section_title", "")
        page_num = doc.get("page_number", 0)
        book = doc.get("book_name", "")

        # Clear source markers for model to reference
        context_part = f"""
### [Джерело {i}]
- Підручник: {book}
- Розділ: {section}
- Тема: {topic}
- Сторінка: {page_num}

{page_text}
---"""
        total_chars += len(context_part)

        # For non-Algebra, still check max_chars
        if not is_algebra and total_chars > max_chars:
            break

        context_parts.append(context_part)

        references.append({
            "source_id": i,
            "book": book,
            "section": section,
            "topic": topic,
            "page": page_num,
        })

    return "\n".join(context_parts), references


# Global instance
_retriever: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """Get singleton retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
    return _retriever
