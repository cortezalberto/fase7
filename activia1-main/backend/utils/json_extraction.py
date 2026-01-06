"""
Robust JSON Extraction Utilities - Cortez88

Provides safe JSON extraction from LLM responses which may contain
additional text, markdown formatting, or malformed JSON.

This replaces fragile regex-based JSON extraction patterns found
throughout the agents layer.
"""
import json
import logging
import re
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str, required_keys: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Safely extract JSON object from text that may contain additional content.

    Uses brace counting instead of regex to handle nested JSON properly.

    Args:
        text: Text containing JSON somewhere within it
        required_keys: Optional list of keys that must be present in the extracted JSON

    Returns:
        Extracted and validated JSON dict, or None if extraction fails

    Example:
        >>> text = "Here is the analysis: {\"score\": 8, \"details\": {\"nested\": true}} Done."
        >>> extract_json_from_text(text)
        {'score': 8, 'details': {'nested': True}}
    """
    if not text or not isinstance(text, str):
        return None

    # Try to find JSON starting with {
    start_idx = text.find('{')
    if start_idx == -1:
        logger.debug("No JSON object found in text (no opening brace)")
        return None

    # Count braces to find the matching closing brace
    brace_count = 0
    end_idx = -1
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == '\\' and in_string:
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == '{':
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    if end_idx == -1:
        logger.warning("Could not find matching closing brace in JSON extraction")
        return None

    json_str = text[start_idx:end_idx]

    try:
        result = json.loads(json_str)

        # Validate required keys if specified
        if required_keys:
            missing_keys = [key for key in required_keys if key not in result]
            if missing_keys:
                logger.warning(
                    "Extracted JSON missing required keys: %s",
                    missing_keys
                )
                # Return partial result anyway, let caller decide

        return result

    except json.JSONDecodeError as e:
        logger.warning(
            "JSON decode error at position %d: %s. Attempting cleanup...",
            e.pos, e.msg
        )
        # Try to clean up common LLM JSON issues
        return _attempt_json_cleanup(json_str)


def _attempt_json_cleanup(json_str: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to fix common JSON formatting issues from LLM responses.

    Common issues:
    - Trailing commas
    - Single quotes instead of double
    - Unquoted keys
    - Control characters in strings
    """
    cleaned = json_str

    # Remove trailing commas before ] or }
    cleaned = re.sub(r',\s*([\]}])', r'\1', cleaned)

    # Try parsing after cleanup
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Replace single quotes with double (risky but sometimes necessary)
    # Only do this if double quotes are not present
    if '"' not in cleaned:
        cleaned_single = cleaned.replace("'", '"')
        try:
            return json.loads(cleaned_single)
        except json.JSONDecodeError:
            pass

    logger.error("JSON cleanup failed, could not parse: %s...", json_str[:100])
    return None


def extract_json_with_fallback(
    text: str,
    fallback_value: Dict[str, Any],
    required_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Extract JSON from text with a fallback value if extraction fails.

    This is the recommended function for agent code where a response
    is always needed.

    Args:
        text: Text containing JSON
        fallback_value: Value to return if extraction fails
        required_keys: Optional keys to validate

    Returns:
        Extracted JSON or fallback_value
    """
    result = extract_json_from_text(text, required_keys)

    if result is None:
        logger.info(
            "Using fallback value for JSON extraction. Text preview: %s...",
            text[:50] if text else "empty"
        )
        return fallback_value

    return result


def safe_get_nested(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Safely get a nested value from a dict without raising KeyError.

    Args:
        data: Dictionary to traverse
        *keys: Sequence of keys to follow
        default: Value to return if any key is missing

    Returns:
        The nested value or default

    Example:
        >>> data = {"a": {"b": {"c": 1}}}
        >>> safe_get_nested(data, "a", "b", "c")
        1
        >>> safe_get_nested(data, "a", "x", "c", default=0)
        0
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


__all__ = [
    "extract_json_from_text",
    "extract_json_with_fallback",
    "safe_get_nested",
]
