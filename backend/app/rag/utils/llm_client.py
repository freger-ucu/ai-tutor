"""
LLM Client for Agentic RAG - multi-provider support.

Supports: Lapa (Mamay), OpenAI, Gemini via OpenAI-compatible API.
Includes LangSmith tracing for observability.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, Any, List, Optional, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from ..config import get_settings
from app.config import settings as app_settings
from app.services.tracing import trace_llm, is_tracing_enabled
from app.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)


def _try_parse_letter_answer(text: str) -> Optional[Dict[str, Any]]:
    """Try to extract a letter answer (A/B/C/D) from text."""
    if not text:
        return None
    text = text.strip()
    # Check if it's just a single letter
    if len(text) == 1 and text.upper() in "ABCD":
        return {"answer": text.upper()}
    # Try pattern like "Відповідь: B" or "Answer: B"
    match = re.search(r'(?:Відповідь|Answer)[:\s]*([ABCD])', text, re.IGNORECASE)
    if match:
        return {"answer": match.group(1).upper()}
    # Try to find standalone letter at the end
    match = re.search(r'\b([ABCD])\s*[.!]?\s*$', text, re.IGNORECASE)
    if match:
        return {"answer": match.group(1).upper()}
    return None


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

    @trace_llm(name="llm_generate_structured")
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[BaseModel],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> Dict[str, Any]:
        """
        Generate with guaranteed schema compliance using structured outputs.

        Uses json_schema response_format for constrained decoding.
        Falls back to basic json_mode if structured outputs not supported.

        Args:
            prompt: The prompt to send
            response_schema: Pydantic model defining the response schema
            temperature: Sampling temperature (default 0.0 for deterministic)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed dict matching the schema
        """
        await self._throttle()

        # Build JSON schema from Pydantic model
        schema = response_schema.model_json_schema()
        # OpenAI requires additionalProperties: false for strict mode
        schema["additionalProperties"] = False

        kwargs = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema.__name__.lower(),
                    "strict": True,
                    "schema": schema
                }
            }
        }

        if "gpt-5" in self.model:
            kwargs["temperature"] = 1
            kwargs["max_completion_tokens"] = max_tokens
            kwargs.pop("max_tokens", None)
        else:
            kwargs["temperature"] = temperature

        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                # On retry, slightly increase temperature to encourage response
                if attempt > 0 and "gpt-5" not in self.model:
                    kwargs["temperature"] = min(0.3, temperature + 0.1 * attempt)

                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                if not content or not content.strip():
                    if attempt < max_retries:
                        logger.warning(f"Empty response on attempt {attempt + 1}, retrying...")
                        await asyncio.sleep(1.0 + attempt * 0.5)  # Longer backoff
                        continue
                    # Last resort: try json_mode fallback
                    logger.warning("[LLMClient.generate_structured] Empty response, trying json_mode fallback")
                    text = await self.generate(prompt, temperature, max_tokens=max_tokens, json_mode=True)
                    if text and text.strip():
                        # Try to extract letter if it's a simple answer
                        parsed = _try_parse_letter_answer(text)
                        if parsed:
                            return parsed
                        return parse_json_response(text, fallback={"answer": "A"}, context="LLMClient.generate_structured")
                    return {"answer": "A", "error": "Empty response after all retries"}
                # Try to parse JSON, but handle simple letter responses
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Model might return just a letter like "B"
                    parsed = _try_parse_letter_answer(content)
                    if parsed:
                        return parsed
                    raise
            except Exception as e:
                if attempt < max_retries:
                    logger.warning(f"Error on attempt {attempt + 1}: {e}, retrying...")
                    await asyncio.sleep(1.0 + attempt * 0.5)
                    continue
                # Fall back to basic json_mode if structured outputs fail
                logger.warning(f"Structured output failed, falling back to json_mode: {e}")
                text = await self.generate(prompt, temperature, max_tokens=max_tokens, json_mode=True)
                return parse_json_response(
                    text,
                    fallback={"answer": 0, "error": "JSON parsing failed"},
                    context="LLMClient.generate_structured"
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


async def generate_structured_safe(
    prompt: str,
    response_schema: Type[BaseModel],
    temperature: float = 0.0,
    default: Optional[Dict] = None
) -> Dict[str, Any]:
    """Safe structured output generation with fallback."""
    client = get_llm_client()
    try:
        return await client.generate_structured(prompt, response_schema, temperature)
    except Exception as e:
        logger.error(f"generate_structured_safe failed: {e}")
        return default or {"error": str(e), "answer": 0, "confidence": 0.1}
