"""
LLM Client for Agentic RAG - multi-provider support.

Supports: Lapa (Mamay), OpenAI, Gemini via OpenAI-compatible API.
Includes LangSmith tracing for observability.
"""

import asyncio
import logging
import re
import time
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from ..config import get_settings
from app.config import settings as app_settings
from app.services.tracing import trace_llm, is_tracing_enabled
from app.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Multi-provider LLM client for Agentic RAG.

    Provider is configured via LLM_PROVIDER env var.
    Supports: lapa (mamay), openai, gemini.
    """

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base_url
        )
        self.embedding_client = AsyncOpenAI(
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_base_url
        )
        self.model = settings.model
        self.embedding_model = settings.embedding_model
        self.provider = app_settings.llm_provider.value
        self.embedding_provider = app_settings.llm_embedding_provider.value
        self._min_request_interval = 12.0 if self.provider == "gemini" else 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._last_request_ts = 0.0
        self._supports_response_format = True
        logger.info(
            "LLMClient initialized: provider=%s, model=%s, embedding_provider=%s, embedding_model=%s",
            self.provider,
            self.model,
            self.embedding_provider,
            self.embedding_model,
        )

    async def _throttle(self) -> None:
        """Throttle requests for providers with strict RPM limits (e.g., Gemini free tier)."""
        if self._min_request_interval <= 0:
            return
        async with self._rate_limit_lock:
            now = time.monotonic()
            wait_s = self._min_request_interval - (now - self._last_request_ts)
            if wait_s > 0:
                await asyncio.sleep(wait_s)
            self._last_request_ts = time.monotonic()

    @trace_llm(name="llm_generate")
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,  # Reduced default
        json_mode: bool = False
    ) -> str:
        """Generate text from LLM."""
        await self._throttle()
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if "gpt-5" in self.model:
            # GPT-5 models only support default temperature (1).
            kwargs["temperature"] = 1
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["temperature"] = temperature
            kwargs["max_tokens"] = max_tokens

        if json_mode and self._supports_response_format:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self.client.chat.completions.create(**kwargs)
        except Exception as e:
            if json_mode and "response_format" in kwargs and "response_format" in str(e):
                self._supports_response_format = False
                kwargs.pop("response_format", None)
                response = await self.client.chat.completions.create(**kwargs)
            else:
                raise
        return response.choices[0].message.content

    async def generate_json(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,  # Short response for JSON
    ) -> Dict[str, Any]:
        """Generate JSON with robust parsing."""
        text = await self.generate(prompt, temperature, max_tokens=max_tokens, json_mode=True)
        return parse_json_response(
            text,
            fallback={"error": "JSON parsing failed", "raw_text": text[:200]},
            context="LLMClient"
        )

    async def embed(self, text: str) -> List[float]:
        """Generate embedding vector."""
        response = await self.embedding_client.embeddings.create(
            input=text,
            model=self.embedding_model,
            encoding_format="float"
        )
        return response.data[0].embedding


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def generate_json_safe(
    prompt: str,
    temperature: float = 0.0,
    default: Optional[Dict] = None
) -> Dict[str, Any]:
    """Safe JSON generation with fallback."""
    client = get_llm_client()
    try:
        return await client.generate_json(prompt, temperature)
    except Exception as e:
        return default or {"error": str(e), "answer_index": 0, "confidence": 0.1}
