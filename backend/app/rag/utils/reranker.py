"""
Cross-Encoder Reranker for Agentic RAG.

Uses BGE-reranker-v2-m3 for high-quality reranking of retrieved documents.
This significantly improves retrieval precision compared to bi-encoder only.

Pipeline: Hybrid top-50 → Reranker top-6 → LLM
"""

import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Lazy import of sentence-transformers to avoid grpcio crash on macOS
# CrossEncoder is loaded on first use, not at module import
_cross_encoder_checked = False
_CrossEncoder = None
CROSS_ENCODER_AVAILABLE = False  # Updated on first check


def _get_cross_encoder_class():
    """Lazy load CrossEncoder to avoid grpcio initialization at module load."""
    global _cross_encoder_checked, _CrossEncoder, CROSS_ENCODER_AVAILABLE
    if not _cross_encoder_checked:
        _cross_encoder_checked = True
        try:
            from sentence_transformers import CrossEncoder
            _CrossEncoder = CrossEncoder
            CROSS_ENCODER_AVAILABLE = True
        except ImportError:
            _CrossEncoder = None
            CROSS_ENCODER_AVAILABLE = False
    return _CrossEncoder


class Reranker:
    """
    Cross-encoder reranker using BGE-reranker-v2-m3.

    Cross-encoders jointly encode query+document pairs for more accurate
    relevance scoring than bi-encoders (which encode separately).

    Trade-off: Higher latency but much better precision.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        """
        Initialize reranker.

        Args:
            model_name: HuggingFace model name. Options:
                - "BAAI/bge-reranker-v2-m3" (multilingual, recommended)
                - "BAAI/bge-reranker-base" (English-focused, faster)
                - "cross-encoder/ms-marco-MiniLM-L-6-v2" (fast, English)
        """
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy-load the model."""
        CrossEncoder = _get_cross_encoder_class()
        if self._model is None and CrossEncoder is not None:
            logger.debug(f" Loading {self.model_name}...")
            self._model = CrossEncoder(self.model_name)
            logger.debug(f" Model loaded")
        return self._model

    def rerank(
        self,
        query: str,
        docs: List[Dict],
        top_k: int = 6,
        max_length: int = 512,
    ) -> List[Dict]:
        """
        Rerank documents using cross-encoder.

        Args:
            query: Search query (question text)
            docs: List of document dicts with 'page_text' field
            top_k: Number of top documents to return
            max_length: Maximum text length per document (truncates)

        Returns:
            Top-k documents sorted by reranker score, with 'rerank_score' added
        """
        _get_cross_encoder_class()  # Ensure availability is checked
        if not CROSS_ENCODER_AVAILABLE or not docs:
            # Fallback: return original order
            return docs[:top_k]

        model = self.model
        if model is None:
            return docs[:top_k]

        # Prepare query-document pairs
        pairs = []
        for doc in docs:
            page_text = doc.get("page_text", "")
            # Truncate to max_length
            if len(page_text) > max_length:
                page_text = page_text[:max_length]
            pairs.append((query, page_text))

        # Get reranker scores
        try:
            scores = model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            logger.debug(f" Error: {e}")
            return docs[:top_k]

        # Add scores to docs
        scored_docs = []
        for doc, score in zip(docs, scores):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(score)
            scored_docs.append(doc_copy)

        # Sort by reranker score (descending)
        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        return scored_docs[:top_k]

    def rerank_with_options(
        self,
        question: str,
        options: List[str],
        docs: List[Dict],
        top_k: int = 6,
        max_length: int = 512,
    ) -> List[Dict]:
        """
        Rerank with option-awareness: boost docs that are relevant to question + options.

        This helps for multiple-choice questions where the answer might be
        mentioned in one of the options.

        Args:
            question: Question text
            options: List of answer options
            docs: Documents to rerank
            top_k: Number to return
            max_length: Max text length

        Returns:
            Reranked documents with combined scores
        """
        _get_cross_encoder_class()  # Ensure availability is checked
        if not CROSS_ENCODER_AVAILABLE or not docs:
            return docs[:top_k]

        model = self.model
        if model is None:
            return docs[:top_k]

        # Score with question only
        q_pairs = [(question, doc.get("page_text", "")[:max_length]) for doc in docs]

        try:
            q_scores = model.predict(q_pairs, show_progress_bar=False)
        except Exception as e:
            logger.debug(f" Error: {e}")
            return docs[:top_k]

        # Score with question + each option (take max)
        option_boost_scores = np.zeros(len(docs))

        for option in options:
            combined_query = f"{question} {option}"
            opt_pairs = [(combined_query, doc.get("page_text", "")[:max_length]) for doc in docs]

            try:
                opt_scores = model.predict(opt_pairs, show_progress_bar=False)
                # Take element-wise max with current boost
                option_boost_scores = np.maximum(option_boost_scores, opt_scores)
            except Exception:
                continue

        # Combine scores: 70% question score + 30% best option score
        combined_scores = 0.7 * np.array(q_scores) + 0.3 * option_boost_scores

        # Add scores to docs
        scored_docs = []
        for i, doc in enumerate(docs):
            doc_copy = doc.copy()
            doc_copy["rerank_score"] = float(combined_scores[i])
            doc_copy["q_score"] = float(q_scores[i])
            doc_copy["option_boost"] = float(option_boost_scores[i])
            scored_docs.append(doc_copy)

        # Sort by combined score
        scored_docs.sort(key=lambda x: x["rerank_score"], reverse=True)

        return scored_docs[:top_k]


# Global instance
_reranker: Optional[Reranker] = None


def get_reranker() -> Reranker:
    """Get singleton reranker instance."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker


def rerank_docs(
    query: str,
    docs: List[Dict],
    top_k: int = 6,
) -> List[Dict]:
    """Convenience function for reranking."""
    reranker = get_reranker()
    return reranker.rerank(query, docs, top_k)
