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


def fix_latex_escapes(json_str: str) -> str:
    """
    Fix LaTeX escape sequences that break JSON parsing.

    LaTeX uses backslashes like \\begin, \\frac which Python JSON
    interprets as invalid escape sequences (\\b = backspace, \\f = formfeed).
    This converts single backslashes to double backslashes inside strings.

    Key insight: We use a prefix list of known LaTeX commands that conflict
    with JSON escapes to distinguish \\frac (LaTeX) from \\f (formfeed).
    """
    # Common LaTeX commands that start with letters that are also JSON escapes.
    # We check if the text after backslash starts with any of these prefixes.
    # Format: commands starting with b, f, n, r, t (the ambiguous JSON escapes)
    latex_prefixes = {
        # \b... commands (JSON \b = backspace)
        'bar', 'begin', 'beta', 'bf', 'big', 'binom', 'bmod', 'bold', 'boldsymbol',
        'bot', 'boxed', 'brace', 'breve', 'bullet',
        # \f... commands (JSON \f = formfeed)
        'frac', 'flat', 'forall', 'footnote',
        # \n... commands (JSON \n = newline)
        'nabla', 'ne', 'neg', 'neq', 'newline', 'newcommand', 'ni', 'not', 'notin',
        'nu', 'nwarrow',
        # \r... commands (JSON \r = carriage return)
        'rangle', 'rceil', 'ref', 'rfloor', 'rho', 'right', 'rightarrow', 'rm',
        # \t... commands (JSON \t = tab)
        'tan', 'tau', 'text', 'textbf', 'textit', 'textrm', 'therefore', 'theta',
        'tilde', 'times', 'to', 'top', 'triangle',
        # Additional common LaTeX commands (not ambiguous with JSON escapes,
        # but handled by the else branch - listed here for documentation)
        # \cdot, \left, \right, \sqrt, \sum, \prod, \int, \lim, \alpha, \gamma, etc.
    }

    result = []
    in_string = False
    i = 0

    while i < len(json_str):
        char = json_str[i]

        if char == '"' and (i == 0 or json_str[i-1] != '\\'):
            in_string = not in_string
            result.append(char)
            i += 1
            continue

        if in_string and char == '\\':
            if i + 1 < len(json_str):
                next_char = json_str[i + 1]
                # Valid JSON escapes that are NOT ambiguous: " /
                # Note: \\ is handled separately above
                safe_json_escapes = {'"', '/'}
                # Ambiguous: b f n r t (could be JSON escape or start of LaTeX)
                ambiguous_escapes = {'b', 'f', 'n', 'r', 't'}

                if next_char == 'u':
                    # \uXXXX unicode escape - check for 4 hex digits
                    if i + 5 < len(json_str) and all(c in '0123456789abcdefABCDEF' for c in json_str[i+2:i+6]):
                        # Valid unicode escape, keep as-is
                        result.append(char)
                        i += 1
                        continue
                    else:
                        # Not valid unicode, likely LaTeX like \underline
                        result.append('\\\\')
                        i += 1
                        continue
                elif next_char in {'(', ')', '[', ']'}:
                    # LaTeX delimiters \( \) \[ \] - keep as-is, they're valid
                    result.append(char)
                    i += 1
                    continue
                elif next_char in ambiguous_escapes:
                    # Check if this matches a known LaTeX command prefix
                    # Extract potential command (letters after backslash)
                    cmd_start = i + 1
                    cmd_end = cmd_start
                    while cmd_end < len(json_str) and json_str[cmd_end].isalpha():
                        cmd_end += 1
                    potential_cmd = json_str[cmd_start:cmd_end]

                    # Check if it's a known LaTeX command
                    is_latex = any(potential_cmd.startswith(prefix) or potential_cmd == prefix
                                   for prefix in latex_prefixes)

                    if is_latex:
                        # It's a LaTeX command - double the backslash
                        result.append('\\\\')
                        i += 1
                        continue
                    else:
                        # It's a JSON escape like \n, \t - keep as-is
                        result.append(char)
                        i += 1
                        continue
                elif next_char == '\\':
                    # Already escaped (\\) - keep both backslashes and skip both
                    result.append('\\\\')
                    i += 2
                    continue
                elif next_char in safe_json_escapes:
                    # Valid JSON escape like \" or \/ - keep as-is
                    result.append(char)
                    i += 1
                    continue
                else:
                    # Not a valid JSON escape - must be LaTeX like \alpha, \cdot
                    result.append('\\\\')
                    i += 1
                    continue
            result.append(char)
            i += 1
            continue

        result.append(char)
        i += 1

    return ''.join(result)


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

    # IMPORTANT: Always fix LaTeX escapes FIRST, before any parsing attempt.
    # This is because \f and \b are valid JSON escapes (formfeed, backspace),
    # but in LLM responses they're almost always LaTeX commands like \frac, \begin.
    # If we parse first, json.loads will convert \frac to formfeed+rac, corrupting the data.
    text = fix_latex_escapes(text)

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
                f"[{context}] JSON decode error after all fixes: {e}" if context
                else f"JSON decode error after all fixes: {e}"
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
