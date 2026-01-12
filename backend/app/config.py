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

    # LLM
    llm_provider: str = "lapa"
    llm_api_key: str = ""
    llm_base_url: str = ""
    llm_model_name: str = ""
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None

    # Phoenix
    phoenix_enabled: bool = False
    phoenix_endpoint: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
