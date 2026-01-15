"""
Configuration for RAG pipeline.

Uses main app settings and provides RAG-specific helpers.
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List

from app.config import settings


class Settings:
    """
    RAG settings wrapper around main app config.

    Provides compatibility interface for existing RAG code.
    """

    @property
    def api_key(self) -> str:
        return settings.llm_api_key

    @property
    def api_base_url(self) -> str:
        return settings.llm_base_url

    @property
    def embedding_api_key(self) -> str:
        return settings.embedding_api_key

    @property
    def embedding_base_url(self) -> str:
        return settings.embedding_base_url

    @property
    def model(self) -> str:
        return settings.llm_model

    @property
    def embedding_model(self) -> str:
        return settings.embedding_model

    @property
    def data_dir(self) -> str:
        return str(settings.data_dir)

    @property
    def embedding_type(self) -> str:
        return settings.rag_embedding_type

    @property
    def retrieval_top_k(self) -> int:
        return settings.rag_retrieval_top_k

    @property
    def retrieval_max_chars(self) -> int:
        return settings.rag_retrieval_max_chars

    @property
    def rrf_k(self) -> int:
        return settings.rag_rrf_k

    @property
    def theory_only(self) -> bool:
        return settings.rag_theory_only

    @property
    def generation_temperature(self) -> float:
        return settings.llm_temperature

    @property
    def max_tokens(self) -> int:
        return settings.llm_max_tokens

    # Agent decision settings (can be overridden via env)
    min_context_quality: float = 0.5
    max_retry_count: int = 1

    # Self-consistency settings
    sc_temperature: float = 0.3
    sc_confidence_threshold: float = 0.7


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get singleton settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


@dataclass
class SubjectConfig:
    """Subject-specific configuration."""

    temperature: float
    always_use_sc: bool  # Always use self-consistency
    question_types: List[str]
    retrieval_boost: float = 1.0
    retrieval_top_k: Optional[int] = None  # Override default top_k if set
    max_context_chars: Optional[int] = None  # Override max chars if set

    # V8: Passage extraction settings
    use_passage_extraction: bool = False     # Enable/disable passage-level extraction
    passage_top_k: int = 5                   # Number of passages to extract
    passage_max_pages: int = 3               # Max unique source pages
    passage_min_length: int = 50             # Min paragraph length (chars)
    passage_max_length: int = 800            # Max paragraph length before split

    # V9: Dual-Field BM25 settings
    use_dual_field_bm25: bool = False        # Enable separate surface/lemma BM25 indices
    bm25_surface_weight: float = 0.5         # Weight for surface tokens (1-alpha for lemma)

    # V9: RRF fusion weights
    rrf_bm25_weight: float = 1.0             # Weight for BM25 in RRF fusion
    rrf_vector_weight: float = 1.0           # Weight for Vector in RRF fusion

    # V9: Query expansion settings
    use_query_expansion: bool = False        # Enable grammar synonym expansion
    max_query_expansions: int = 3            # Max synonym phrases to add

    # V9: Enhanced passage scoring
    use_enhanced_passage_scoring: bool = False  # Enable rule-density bonuses

    # V9: Term matching rerank
    use_term_matching_rerank: bool = False   # Enable term matching bonus in reranking


# Subject-specific configurations
SUBJECT_CONFIGS = {
    "Українська мова": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,  # Disabled SC - it was making things worse
        question_types=["punctuation", "syntax", "morphology", "vocabulary", "spelling"],
        retrieval_boost=1.5,  # V7: Increased for better coverage
        retrieval_top_k=40,   # V7: More candidates for reranking
        max_context_chars=3000,  # V8: Reduced - focused passages need less space
        # V8: Passage extraction for better rule-dense context
        use_passage_extraction=True,  # A/B TEST: with passages
        passage_top_k=5,
        passage_max_pages=3,
        passage_min_length=50,
        passage_max_length=800,
        # V9: Sprint 1 - Dual-Field BM25 + RRF Weights
        use_dual_field_bm25=True,       # V9.1: Fixed with rank-based fusion
        bm25_surface_weight=0.5,        # 50% surface + 50% lemma
        rrf_bm25_weight=1.2,            # BM25 slightly more important for grammar
        rrf_vector_weight=1.0,          # Keep vector at default
    ),
    "Українська література": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,  # Disabled SC
        question_types=["analysis", "author", "work", "character"],
        retrieval_boost=1.0,
    ),
    "Алгебра": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,  # Only on low confidence
        question_types=["equation", "function", "progression", "inequality", "expression"],
        retrieval_boost=1.0,
    ),
    "Геометрія": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,
        question_types=["theorem", "proof", "calculation", "construction"],
        retrieval_boost=1.0,
    ),
    "Історія України": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,
        question_types=["date", "fact", "cause_effect", "document", "person", "event"],
        retrieval_boost=1.2,
    ),
    "Всесвітня історія": SubjectConfig(
        temperature=0.0,
        always_use_sc=False,
        question_types=["date", "fact", "cause_effect", "document", "person", "event"],
        retrieval_boost=1.2,
    ),
}


def get_subject_config(subject: str) -> SubjectConfig:
    """Get configuration for a subject."""
    return SUBJECT_CONFIGS.get(
        subject,
        SubjectConfig(
            temperature=0.0,
            always_use_sc=False,
            question_types=["general"],
        )
    )


# Paths helper
def get_data_path(filename: str = "") -> Path:
    """Get path to data directory or file."""
    base = Path(settings.data_dir)
    return base / filename if filename else base


def get_embedding_path(filename: str) -> Path:
    """Get path to embedding-specific file in embeddings directory."""
    return get_data_path("embeddings") / filename
