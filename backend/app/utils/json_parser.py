"""
Centralized JSON parsing utilities for LLM responses.

Handles common patterns:
- JSON wrapped in markdown code blocks (```json ... ```)
- Raw JSON with extra text
- Malformed JSON with unescaped characters
"""

import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def strip_markdown_code_blocks(text: str) -> str:
    """
    Remove markdown code block wrappers from text.

    Handles:
    - ```json ... ```
    - ``` ... ```
    - Plain text (returns as-is)
    - Nested code blocks inside JSON strings

    Args:
        text: Input text possibly wrapped in code blocks

    Returns:
        Text with outer code block markers removed
    """
    text = text.strip()

    # Handle ```json blocks - find the LAST ``` to handle nested blocks
    if text.startswith("```json"):
        text = text[7:].strip()  # Remove ```json
        # Find the last ``` which closes the outer block
        last_fence = text.rfind("\n```")
        if last_fence != -1:
            text = text[:last_fence]
        elif text.endswith("```"):
            text = text[:-3]
        return text.strip()

    # Handle plain ``` blocks
    if text.startswith("```"):
        # Remove opening fence and optional language identifier
        lines = text.split("\n", 1)
        if len(lines) > 1:
            text = lines[1]
        else:
            text = text[3:]
        # Find the last ``` which closes the outer block
        last_fence = text.rfind("\n```")
        if last_fence != -1:
            text = text[:last_fence]
        elif text.endswith("```"):
            text = text[:-3]
        return text.strip()

    return text


def extract_json_object(text: str) -> Optional[str]:
    """
    Extract JSON object string from text containing extra content.

    Finds the outermost { } pair in the text.

    Args:
        text: Text potentially containing a JSON object

    Returns:
        The JSON string if found, None otherwise
    """
    if "{" not in text or "}" not in text:
        return None

    start = text.find("{")
    end = text.rfind("}") + 1

    if start < end:
        return text[start:end]

    return None


def fix_json_newlines(json_str: str) -> str:
    """
    Fix unescaped newlines inside JSON string values.

    LLMs often return JSON with literal newlines in string values,
    which is invalid JSON. This function escapes them.
    """
    result = []
    in_string = False
    escape_next = False

    for char in json_str:
        if escape_next:
            result.append(char)
            escape_next = False
            continue

        if char == '\\':
            result.append(char)
            escape_next = True
            continue

        if char == '"':
            in_string = not in_string
            result.append(char)
            continue

        if in_string and char == '\n':
            result.append('\\n')
            continue

        result.append(char)

    return ''.join(result)


def parse_json_response(
    response: str,
    fallback: Optional[dict] = None,
    context: str = ""
) -> dict:
    """
    Parse JSON from an LLM response with multiple fallback strategies.

    Attempts:
    1. Direct JSON parse
    2. Strip markdown code blocks, then parse
    3. Extract JSON object from text, then parse
    4. Fix unescaped newlines, then parse
    5. Return fallback dict if all parsing fails

    Args:
        response: Raw LLM response text
        fallback: Dict to return if parsing fails (default: empty dict)
        context: Optional context string for logging errors

    Returns:
        Parsed dict, or fallback if parsing fails
    """
    if fallback is None:
        fallback = {}

    if not response or not response.strip():
        logger.warning(f"[{context}] Empty response received" if context else "Empty response received")
        return fallback

    text = response.strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code blocks
    cleaned = strip_markdown_code_blocks(text)
    if cleaned != text:
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 3: Extract JSON object
    json_str = extract_json_object(cleaned)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Strategy 4: Fix unescaped newlines in JSON strings
        try:
            fixed = fix_json_newlines(json_str)
            return json.loads(fixed)
        except json.JSONDecodeError as e:
            logger.debug(
                f"[{context}] JSON decode error after newline fix: {e}" if context
                else f"JSON decode error after newline fix: {e}"
            )

    # All strategies failed - log first 500 chars for debugging
    preview = response[:500] if len(response) > 500 else response
    logger.warning(
        f"[{context}] Failed to parse JSON from response (length={len(response)}). Preview: {preview!r}"
        if context else f"Failed to parse JSON from response (length={len(response)}). Preview: {preview!r}"
    )
    return fallback


def parse_json_with_regex_fallback(
    response: str,
    field_patterns: dict[str, str],
    defaults: dict[str, Any],
    context: str = ""
) -> dict:
    """
    Parse JSON with regex fallback for specific fields.

    When JSON parsing fails, attempts to extract fields using regex patterns.
    Useful for handling LLM responses with unescaped newlines in strings.

    Args:
        response: Raw LLM response text
        field_patterns: Dict mapping field names to regex patterns
        defaults: Dict with default values for each field
        context: Optional context string for logging

    Returns:
        Parsed dict with all fields (parsed or defaults)
    """
    # First try standard parsing
    result = parse_json_response(response, fallback=None, context=context)
    if result is not None:
        # Fill in any missing fields from defaults
        for key, default in defaults.items():
            if key not in result:
                result[key] = default
        return result

    # Fallback to regex extraction
    result = {}
    cleaned = strip_markdown_code_blocks(response)
    json_str = extract_json_object(cleaned) or cleaned

    for field_name, pattern in field_patterns.items():
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            value = match.group(1)
            # Unescape common escape sequences
            value = value.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            result[field_name] = value
        else:
            result[field_name] = defaults.get(field_name, "")

    return result
