"""
LLM generation node factory.

Creates LLM nodes with configurable prompt builders and output parsing.
Integrates with existing LLMClient and provides LangSmith tracing.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, Callable, Optional, TypeVar, Generic

from app.services.tracing import trace_chain
from app.rag.utils.llm_client import get_llm_client
from app.utils.json_parser import parse_json_response

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class LLMConfig:
    """Configuration for LLM generation node."""

    temperature: float = 0.0
    max_tokens: int = 2000
    json_mode: bool = False
    trace_name: str = "llm_generate"


def create_llm_node(
    prompt_builder: Callable[[Dict[str, Any]], str],
    output_parser: Optional[Callable[[str], Dict[str, Any]]] = None,
    config: LLMConfig = LLMConfig(),
    output_key: str = "llm_output",
    increment_counter: bool = True,
    counter_key: str = "llm_calls_count",
) -> Callable:
    """
    Factory function to create LLM generation node.

    Args:
        prompt_builder: Function that takes state and returns prompt string
        output_parser: Optional function to parse LLM response into structured output
        config: LLM configuration
        output_key: State key for output
        increment_counter: Whether to increment LLM call counter
        counter_key: State key for LLM call counter

    Returns:
        Async node function compatible with LangGraph
    """

    @trace_chain(name=config.trace_name)
    async def llm_generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response from LLM using prompt builder."""
        client = get_llm_client()

        # Build prompt from state
        prompt = prompt_builder(state)

        if not prompt:
            logger.warning("Empty prompt generated")
            return {output_key: None}

        # Generate response
        if config.json_mode:
            response = await client.generate_json(
                prompt=prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            parsed = response
        else:
            response = await client.generate(
                prompt=prompt,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            # Parse response if parser provided
            if output_parser:
                parsed = output_parser(response)
            else:
                parsed = response

        # Build result
        result = {output_key: parsed}

        # Increment counter if requested
        if increment_counter:
            current_count = state.get(counter_key, 0)
            result[counter_key] = current_count + 1

        return result

    return llm_generate_node


def create_json_llm_node(
    prompt_builder: Callable[[Dict[str, Any]], str],
    required_fields: Optional[list] = None,
    default_values: Optional[Dict[str, Any]] = None,
    config: LLMConfig = None,
    output_key: str = "llm_output",
) -> Callable:
    """
    Create LLM node that outputs parsed JSON with validation.

    Args:
        prompt_builder: Function that takes state and returns prompt string
        required_fields: List of required fields in JSON output
        default_values: Default values if parsing fails
        config: LLM configuration (defaults to json_mode=True)
        output_key: State key for output

    Returns:
        Async node function compatible with LangGraph
    """
    if config is None:
        config = LLMConfig(json_mode=True)

    defaults = default_values or {}

    def json_parser(response: str) -> Dict[str, Any]:
        """Parse JSON response with fallback to defaults."""
        parsed = parse_json_response(response, fallback=defaults)

        # Validate required fields
        if required_fields:
            for field in required_fields:
                if field not in parsed:
                    logger.warning(f"Missing required field: {field}")
                    parsed[field] = defaults.get(field)

        return parsed

    return create_llm_node(
        prompt_builder=prompt_builder,
        output_parser=json_parser if not config.json_mode else None,
        config=config,
        output_key=output_key,
    )


def create_batch_llm_node(
    prompt_builder: Callable[[Dict[str, Any]], str],
    item_parser: Callable[[Dict[str, Any]], list],
    config: LLMConfig = None,
    output_key: str = "generated_items",
    counter_key: str = "llm_calls_count",
) -> Callable:
    """
    Create LLM node for batch generation (e.g., multiple questions).

    Args:
        prompt_builder: Function that takes state and returns prompt string
        item_parser: Function to extract list of items from parsed response
        config: LLM configuration
        output_key: State key for list of generated items
        counter_key: State key for LLM call counter

    Returns:
        Async node function compatible with LangGraph
    """
    if config is None:
        config = LLMConfig(json_mode=True, max_tokens=4000)

    @trace_chain(name=config.trace_name or "batch_llm_generate")
    async def batch_generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate batch of items from LLM."""
        client = get_llm_client()

        prompt = prompt_builder(state)
        if not prompt:
            return {output_key: [], counter_key: state.get(counter_key, 0)}

        response = await client.generate_json(
            prompt=prompt,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

        # Parse items from response
        items = item_parser(response)

        return {
            output_key: items,
            counter_key: state.get(counter_key, 0) + 1,
        }

    return batch_generate_node
