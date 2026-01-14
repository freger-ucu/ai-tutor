"""
LLM Client for Agentic RAG - simplified wrapper for LapaLLM.

Includes LangSmith tracing for observability.
"""

import logging
import re
from typing import Dict, Any, List, Optional

from openai import AsyncOpenAI

from ..config import get_settings
from app.services.tracing import trace_llm, is_tracing_enabled
from app.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Simplified LLM client for Agentic RAG.

    Uses LapaLLM via OpenAI-compatible API.
    """

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.api_key,
            base_url=settings.api_base_url
        )
        self.model = settings.model
        self.embedding_model = settings.embedding_model

    @trace_llm(name="llm_generate")
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 500,  # Reduced default
        json_mode: bool = False
    ) -> str:
        """Generate text from LLM."""
        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
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
        response = await self.client.embeddings.create(
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
