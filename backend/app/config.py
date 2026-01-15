"""
Application Configuration

Loads and validates environment variables using pydantic-settings.
"""

from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    LAPA = "lapa"
    OPENAI = "openai"
    GEMINI = "gemini"


# Provider-specific configurations
PROVIDER_CONFIGS = {
    LLMProvider.LAPA: {
        "base_url": "http://146.59.127.106:4000",
        "default_model": "mamay",
    },
    LLMProvider.OPENAI: {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
    },
    LLMProvider.GEMINI: {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.0-flash",
    },
}


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

    # LLM Provider Selection
    llm_provider: LLMProvider = LLMProvider.LAPA

    # Provider-specific API keys
    lapa_api_key: str = ""
    lapa_base_url: str = "http://146.59.127.106:4000"
    lapa_model: str = "mamay"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Embedding (stays on Lapa for now)
    llm_embedding_model: str = "text-embedding-qwen"

    # Generation defaults
    llm_temperature: float = 0.0
    llm_max_tokens: int = 500

    @property
    def llm_api_key(self) -> str:
        """Get API key for current provider."""
        if self.llm_provider == LLMProvider.LAPA:
            return self.lapa_api_key
        elif self.llm_provider == LLMProvider.OPENAI:
            return self.openai_api_key
        elif self.llm_provider == LLMProvider.GEMINI:
            return self.gemini_api_key
        return ""

    @property
    def llm_base_url(self) -> str:
        """Get base URL for current provider."""
        if self.llm_provider == LLMProvider.LAPA:
            return self.lapa_base_url
        return PROVIDER_CONFIGS[self.llm_provider]["base_url"]

    @property
    def llm_model(self) -> str:
        """Get model name for current provider."""
        if self.llm_provider == LLMProvider.LAPA:
            return self.lapa_model
        elif self.llm_provider == LLMProvider.OPENAI:
            return self.openai_model
        elif self.llm_provider == LLMProvider.GEMINI:
            return self.gemini_model
        return PROVIDER_CONFIGS[self.llm_provider]["default_model"]

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

    # LangSmith
    langsmith_enabled: bool = True
    langsmith_api_key: str = ""
    langsmith_project: str = "ai-tutor"
    langsmith_endpoint: str = "https://api.smith.langchain.com"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
