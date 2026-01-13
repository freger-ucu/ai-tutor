"""
Application Configuration

Loads and validates environment variables using pydantic-settings.
"""

from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "AI Tutor"
    app_version: str = "0.1.0"
    debug: bool = True
    app_env: Literal["development", "production"] = "development"

    # Backend
    backend_port: int = 8000

    # Data paths
    data_dir: Path = Path("data")

    @property
    def scores_path(self) -> Path:
        """Path to benchmark scores parquet file."""
        return self.data_dir / "benchmark_scores.parquet"

    @property
    def absences_path(self) -> Path:
        """Path to benchmark absences parquet file."""
        return self.data_dir / "benchmark_absences.parquet"

    @property
    def toc_dir(self) -> Path:
        """Path to table of contents directory."""
        return self.data_dir / "toc"

    @property
    def pages_dir(self) -> Path:
        """Path to textbook pages directory."""
        return self.data_dir / "pages"

    @property
    def embeddings_dir(self) -> Path:
        """Path to embeddings directory."""
        return self.data_dir / "embeddings"

    # LLM Configuration
    llm_provider: str = "lapa"
    llm_api_key: str = ""
    llm_base_url: str = "http://146.59.127.106:4000"
    llm_model: str = "mamay"
    llm_embedding_model: str = "text-embedding-qwen"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 500

    # RAG Configuration
    rag_embedding_type: str = "qwen"  # "qwen" or "gemini"
    rag_retrieval_top_k: int = 4
    rag_retrieval_max_chars: int = 4000
    rag_rrf_k: int = 60
    rag_theory_only: bool = True

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None

    # Phoenix
    phoenix_enabled: bool = False
    phoenix_endpoint: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
