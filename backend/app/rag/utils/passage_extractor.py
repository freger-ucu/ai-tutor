"""
Passage-level extraction for Ukrainian language questions.

After cross-encoder reranking, extract only the most relevant paragraphs
instead of full page text. This reduces noise and helps LLM focus on
the specific grammar rule needed.

V8 Feature: Expected +5-15% accuracy improvement on Ukrainian language.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re

# BM25 for passage ranking
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    BM25Okapi = None


@dataclass
class PassageConfig:
    """Configuration for passage extraction."""

    # Splitting parameters
    min_paragraph_length: int = 50        # Min chars for a paragraph
    max_paragraph_length: int = 800       # Max chars before forced split
    split_on_sentences: bool = False      # True = sentence-level, False = paragraph-level

    # Selection parameters
    top_k_passages: int = 5               # Number of passages to return
    max_pages_for_passages: int = 3       # Max unique pages in final selection
    pages_to_process: int = 8             # Top reranked pages to process

    # Query enhancement
    include_best_option: bool = True      # Add best answer option to query

    # Output
    max_context_chars: int = 3000         # Max total chars in output


@dataclass
class Passage:
    """A single extracted passage with metadata."""
    text: str
    page_number: int
    topic_title: str
    book_name: str
    book_topic_id: str
    page_id: int
    position_in_page: int       # Order within original page
    bm25_score: float = 0.0     # Relevance score


class PassageExtractor:
    """
    Extract relevant passages from reranked pages using BM25.

    Pipeline:
    1. Take top-N pages from cross-encoder reranking
    2. Split each page into paragraphs
    3. Build BM25 index on all paragraphs
    4. Query with question + best_option
    5. Return top-K passages with source attribution
    """

    def __init__(self, config: Optional[PassageConfig] = None):
        self.config = config or PassageConfig()
        self._morph_analyzer = None

    def _get_morph_analyzer(self):
        """Lazy initialization of Ukrainian morphology analyzer."""
        if self._morph_analyzer is None:
            try:
                import pymorphy2
                self._morph_analyzer = pymorphy2.MorphAnalyzer(lang='uk')
            except Exception:
                self._morph_analyzer = None
        return self._morph_analyzer

    def extract_passages(
        self,
        reranked_docs: List[Dict],
        question: str,
        answers: List[str] = None,
        config: Optional[PassageConfig] = None
    ) -> Tuple[List[Passage], Dict]:
        """
        Extract relevant passages from reranked documents.

        Args:
            reranked_docs: Documents from cross-encoder reranking
            question: Original question text
            answers: Answer options (for query enhancement)
            config: Optional override config

        Returns:
            Tuple of (list of Passage objects, metadata dict)
        """
        cfg = config or self.config

        if not BM25_AVAILABLE:
            # Fallback: return first N pages as-is
            return self._fallback_extraction(reranked_docs, cfg)

        # Step 1: Split pages into paragraphs
        all_passages = self._split_all_pages(
            reranked_docs[:cfg.pages_to_process], cfg
        )

        if not all_passages:
            return [], {"error": "no_passages_extracted"}

        # Step 2: Build BM25 index
        tokenized_passages = [
            self._tokenize_ukrainian(p.text)
            for p in all_passages
        ]
        bm25 = BM25Okapi(tokenized_passages)

        # Step 3: Build query (question + best option if available)
        query = self._build_query(question, answers, cfg)
        query_tokens = self._tokenize_ukrainian(query)

        # Step 4: Score and rank passages
        scores = bm25.get_scores(query_tokens)
        for i, passage in enumerate(all_passages):
            passage.bm25_score = float(scores[i])

        # Step 5: Select top passages with page diversity
        selected = self._select_diverse_passages(all_passages, cfg)

        metadata = {
            "total_passages": len(all_passages),
            "query_used": query,
            "pages_processed": min(len(reranked_docs), cfg.pages_to_process),
            "passages_selected": len(selected),
        }

        return selected, metadata

    def _split_all_pages(
        self,
        docs: List[Dict],
        cfg: PassageConfig
    ) -> List[Passage]:
        """Split all documents into passages."""
        all_passages = []

        for doc in docs:
            page_text = doc.get("page_text", "")
            page_passages = self._split_page(page_text, cfg)

            for i, text in enumerate(page_passages):
                passage = Passage(
                    text=text,
                    page_number=doc.get("page_number", 0),
                    topic_title=doc.get("topic_title", ""),
                    book_name=doc.get("book_name", ""),
                    book_topic_id=doc.get("book_topic_id", ""),
                    page_id=doc.get("page_id", 0),
                    position_in_page=i,
                )
                all_passages.append(passage)

        return all_passages

    def _split_page(self, text: str, cfg: PassageConfig) -> List[str]:
        """
        Split a page into paragraphs or sentences.

        For Ukrainian grammar textbooks:
        - Paragraphs often contain one rule
        - Bullet points and numbered lists are important
        """
        if cfg.split_on_sentences:
            return self._split_into_sentences(text, cfg)
        else:
            return self._split_into_paragraphs(text, cfg)

    def _split_into_paragraphs(self, text: str, cfg: PassageConfig) -> List[str]:
        """Split text into paragraphs."""
        # Split on double newlines or specific markers
        paragraphs = re.split(r'\n\s*\n|\n(?=[•\-\d]+\.?\s)|(?<=\.)\s*\n(?=[А-ЯІЇЄҐ])', text)

        result = []
        for para in paragraphs:
            para = para.strip()
            if len(para) < cfg.min_paragraph_length:
                continue

            # If paragraph too long, split further
            if len(para) > cfg.max_paragraph_length:
                # Split on sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', para)
                current = ""
                for sent in sentences:
                    if len(current) + len(sent) > cfg.max_paragraph_length:
                        if current:
                            result.append(current.strip())
                        current = sent
                    else:
                        current = (current + " " + sent).strip()
                if current and len(current) >= cfg.min_paragraph_length:
                    result.append(current)
            else:
                result.append(para)

        return result

    def _split_into_sentences(self, text: str, cfg: PassageConfig) -> List[str]:
        """Split text into sentences (alternative mode)."""
        sentences = re.split(r'(?<=[.!?])\s+', text)

        result = []
        current = ""
        for sent in sentences:
            sent = sent.strip()
            if not sent:
                continue

            # Group short sentences together
            if len(current) + len(sent) < cfg.min_paragraph_length:
                current = (current + " " + sent).strip()
            else:
                if current:
                    result.append(current)
                current = sent

        if current and len(current) >= cfg.min_paragraph_length // 2:
            result.append(current)

        return result

    def _build_query(
        self,
        question: str,
        answers: List[str],
        cfg: PassageConfig
    ) -> str:
        """
        Build search query from question and best option.

        For grammar questions, the answer options often contain
        the key terms that should match the rule.
        """
        query = question

        if cfg.include_best_option and answers:
            # Include first 2 options (often most relevant)
            for ans in answers[:2]:
                if ans and len(ans) < 100:  # Skip very long options
                    query += " " + ans

        return query

    def _tokenize_ukrainian(self, text: str) -> List[str]:
        """
        Ukrainian tokenizer with lemmatization.

        Reuses the approach from hybrid_retriever.py.
        """
        if not isinstance(text, str):
            return []

        # Minimal stopwords for grammar context
        stopwords = {
            'і', 'в', 'на', 'з', 'за', 'до', 'для', 'про', 'при',
            'це', 'він', 'вона', 'воно', 'вони', 'ми', 'ви',
            'його', 'її', 'їх', 'цей', 'цього', 'після', 'під', 'над',
        }

        text = text.lower()

        # Replace punctuation
        for char in '.,;:!?()[]{}«»"\'-/\\':
            text = text.replace(char, ' ')

        raw_tokens = text.split()
        tokens = [t for t in raw_tokens if len(t) >= 1 and t not in stopwords]

        # Apply lemmatization
        morph = self._get_morph_analyzer()
        if morph is not None:
            result = []
            for token in tokens:
                result.append(token)  # Keep surface form
                try:
                    parsed = morph.parse(token)
                    if parsed:
                        lemma = parsed[0].normal_form
                        if lemma != token and lemma not in stopwords:
                            result.append(lemma)
                except Exception:
                    pass
            return result

        return tokens

    def _select_diverse_passages(
        self,
        passages: List[Passage],
        cfg: PassageConfig
    ) -> List[Passage]:
        """
        Select top passages with page diversity constraint.

        Ensures passages come from at most cfg.max_pages_for_passages
        different pages to maintain source diversity.
        """
        # Sort by BM25 score
        sorted_passages = sorted(passages, key=lambda p: p.bm25_score, reverse=True)

        selected = []
        pages_used = set()
        total_chars = 0

        for passage in sorted_passages:
            if len(selected) >= cfg.top_k_passages:
                break

            if total_chars + len(passage.text) > cfg.max_context_chars:
                continue

            # Page diversity constraint
            page_key = (passage.page_id, passage.page_number)
            if len(pages_used) >= cfg.max_pages_for_passages and page_key not in pages_used:
                continue

            selected.append(passage)
            pages_used.add(page_key)
            total_chars += len(passage.text)

        # Sort by original position for coherent reading order
        selected.sort(key=lambda p: (p.page_number, p.position_in_page))

        return selected

    def _fallback_extraction(
        self,
        docs: List[Dict],
        cfg: PassageConfig
    ) -> Tuple[List[Passage], Dict]:
        """Fallback when BM25 not available: return truncated pages."""
        passages = []
        total_chars = 0

        for doc in docs[:cfg.max_pages_for_passages]:
            text = doc.get("page_text", "")[:cfg.max_context_chars // cfg.max_pages_for_passages]

            if total_chars + len(text) > cfg.max_context_chars:
                break

            passage = Passage(
                text=text,
                page_number=doc.get("page_number", 0),
                topic_title=doc.get("topic_title", ""),
                book_name=doc.get("book_name", ""),
                book_topic_id=doc.get("book_topic_id", ""),
                page_id=doc.get("page_id", 0),
                position_in_page=0,
            )
            passages.append(passage)
            total_chars += len(text)

        return passages, {"fallback": True, "reason": "bm25_not_available"}


# Global instance
_passage_extractor: Optional[PassageExtractor] = None


def get_passage_extractor() -> PassageExtractor:
    """Get singleton passage extractor instance."""
    global _passage_extractor
    if _passage_extractor is None:
        _passage_extractor = PassageExtractor()
    return _passage_extractor


def format_context_with_passages(
    passages: List[Passage],
    topics: List[Dict],
    max_chars: int = 3000
) -> Tuple[str, List[Dict]]:
    """
    Format extracted passages into context string.

    Similar to format_context_with_topics but for passage-level content.
    Preserves source attribution (page number, topic) for each passage.
    """
    # Build topics summary
    topics_summary = []
    for i, topic in enumerate(topics[:3], 1):
        subtopics_str = ", ".join(topic.get("subtopics", [])[:5])
        topics_summary.append(
            f"{i}. {topic['topic_title']} (score: {topic['score']:.2f})\n"
            f"   Підтеми: {subtopics_str}"
        )

    topics_section = "### ЗНАЙДЕНІ ТЕМИ:\n" + "\n".join(topics_summary)

    # Build passages section
    context_parts = [topics_section, "\n### РЕЛЕВАНТНІ УРИВКИ:\n"]
    references = []
    total_chars = len(topics_section) + 50

    for i, passage in enumerate(passages, 1):
        if total_chars + len(passage.text) > max_chars:
            break

        context_part = f"""
[Уривок {i}]
- Тема: {passage.topic_title}
- Сторінка: {passage.page_number}
- Підручник: {passage.book_name}

{passage.text}
---"""

        context_parts.append(context_part)
        total_chars += len(context_part)

        references.append({
            "source_id": i,
            "topic": passage.topic_title,
            "page": passage.page_number,
            "book": passage.book_name,
            "is_passage": True,
        })

    return "\n".join(context_parts), references
