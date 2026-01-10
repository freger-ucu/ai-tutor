"""
Application Configuration

Loads and validates environment variables using pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    debug: bool = True
    app_env: str = "development"

    # Backend
    backend_port: int = 8000

    # LLM
    llm_provider: str = "lapa"
    llm_api_key: str = ""
    llm_base_url: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Phoenix
    phoenix_enabled: bool = False
    phoenix_endpoint: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
