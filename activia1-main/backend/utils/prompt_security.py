"""
Prompt Security Utilities - Centralized prompt injection detection.

FIX Cortez73 (MED-004): Centralized and improved prompt injection detection.

Provides:
- detect_prompt_injection: Detect common prompt injection patterns
- sanitize_for_llm: Prepare user input for safe LLM processing

Usage:
    from backend.utils.prompt_security import detect_prompt_injection

    if detect_prompt_injection(user_input):
        return "Lo siento, no puedo procesar ese tipo de solicitud."
"""
import base64
import re
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


# ==================== Pattern Categories ====================

# System instruction override attempts
OVERRIDE_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "forget your instructions",
    "override your programming",
    "bypass your restrictions",
    "ignore your training",
    "ignore your rules",
    "new instructions:",
    "updated instructions:",
    "system:",
    "assistant:",
    "user:",
    "[system]",
    "[assistant]",
]

# Persona manipulation attempts
PERSONA_PATTERNS = [
    "you are now",
    "pretend you are",
    "act as if you",
    "roleplay as",
    "from now on you",
    "you are no longer",
    "behave as",
    "simulate being",
    "impersonate",
    "play the role of",
    "imagine you are",
    "assume the identity",
]

# Prompt leaking attempts
LEAKING_PATTERNS = [
    "repeat your instructions",
    "show me your prompt",
    "reveal your system prompt",
    "what are your instructions",
    "show your configuration",
    "print your prompt",
    "display your rules",
    "output your training",
    "echo your instructions",
    "tell me your prompt",
]

# Jailbreak attempts
JAILBREAK_PATTERNS = [
    "dan mode",
    "developer mode",
    "jailbreak",
    "do anything now",
    "unrestricted mode",
    "no filter mode",
    "bypass safety",
    "disable safety",
    "disable content filter",
    "remove restrictions",
    "sudo mode",
    "admin mode",
    "god mode",
]

# Code injection attempts (especially dangerous for code evaluators)
CODE_INJECTION_PATTERNS = [
    "import os",
    "import subprocess",
    "exec(",
    "eval(",
    "__import__",
    "os.system",
    "subprocess.run",
    "subprocess.call",
    "open('/etc",
    "open('c:\\\\",
    "rm -rf",
    "del /f",
    "format c:",
]

# Delimiter injection attempts
DELIMITER_PATTERNS = [
    "```",
    "---",
    "===",
    "###",
    "***",
]

# Multi-language injection (Spanish context)
SPANISH_INJECTION_PATTERNS = [
    "ignora las instrucciones anteriores",
    "olvida tus instrucciones",
    "cambia tu comportamiento",
    "ahora eres",
    "actua como si fueras",
    "muestra tu prompt",
    "revela tus instrucciones",
]


# ==================== Detection Functions ====================

def detect_prompt_injection(
    prompt: str,
    check_code: bool = False,
    check_delimiters: bool = True
) -> bool:
    """
    Detect common prompt injection patterns.

    FIX Cortez73 (MED-004): Enhanced detection with more patterns
    and configurable strictness levels.

    Args:
        prompt: User input to analyze
        check_code: If True, also check for code injection patterns
        check_delimiters: If True, check for delimiter injection

    Returns:
        True if injection pattern detected, False otherwise
    """
    if not prompt:
        return False

    # Normalize for case-insensitive matching
    lower_prompt = prompt.lower()

    # Check all pattern categories
    all_patterns: List[str] = []
    all_patterns.extend(OVERRIDE_PATTERNS)
    all_patterns.extend(PERSONA_PATTERNS)
    all_patterns.extend(LEAKING_PATTERNS)
    all_patterns.extend(JAILBREAK_PATTERNS)
    all_patterns.extend(SPANISH_INJECTION_PATTERNS)

    if check_code:
        all_patterns.extend(CODE_INJECTION_PATTERNS)

    # Check for pattern matches
    for pattern in all_patterns:
        if pattern in lower_prompt:
            logger.warning(
                "Prompt injection pattern detected: '%s'",
                pattern[:20] + "..." if len(pattern) > 20 else pattern
            )
            return True

    # Check for delimiter abuse (multiple delimiters suggesting prompt structure)
    if check_delimiters:
        delimiter_count = 0
        for delimiter in DELIMITER_PATTERNS:
            if delimiter in prompt:
                delimiter_count += 1
        if delimiter_count >= 2:
            logger.warning(
                "Multiple delimiters detected, possible injection: %d types",
                delimiter_count
            )
            return True

    # Check for base64 encoded attempts
    if _contains_base64_injection(prompt):
        logger.warning("Base64 encoded injection attempt detected")
        return True

    return False


def _contains_base64_injection(prompt: str) -> bool:
    """
    Detect base64 encoded injection attempts.

    Some attackers encode malicious prompts in base64 to bypass filters.
    """
    import base64

    # Look for base64-like patterns
    base64_pattern = re.compile(r'[A-Za-z0-9+/]{20,}={0,2}')
    matches = base64_pattern.findall(prompt)

    for match in matches:
        try:
            decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
            # Check if decoded content contains injection patterns
            if any(pattern in decoded.lower() for pattern in OVERRIDE_PATTERNS[:5]):
                return True
        except (ValueError, base64.binascii.Error, UnicodeDecodeError):
            # FIX Cortez74: More specific exception handling for base64 decode failures
            continue

    return False


def get_injection_category(prompt: str) -> Optional[str]:
    """
    Identify the category of a detected injection.

    Args:
        prompt: User input to analyze

    Returns:
        Category name if injection detected, None otherwise
    """
    if not prompt:
        return None

    lower_prompt = prompt.lower()

    categories = [
        (OVERRIDE_PATTERNS, "system_override"),
        (PERSONA_PATTERNS, "persona_manipulation"),
        (LEAKING_PATTERNS, "prompt_leaking"),
        (JAILBREAK_PATTERNS, "jailbreak_attempt"),
        (CODE_INJECTION_PATTERNS, "code_injection"),
        (SPANISH_INJECTION_PATTERNS, "spanish_injection"),
    ]

    for patterns, category in categories:
        for pattern in patterns:
            if pattern in lower_prompt:
                return category

    return None


def sanitize_for_logging(prompt: str, max_length: int = 100) -> str:
    """
    Sanitize prompt for safe logging (remove potential secrets/PII).

    Args:
        prompt: User input to sanitize
        max_length: Maximum length of sanitized output

    Returns:
        Sanitized string safe for logging
    """
    if not prompt:
        return ""

    # Truncate
    sanitized = prompt[:max_length]
    if len(prompt) > max_length:
        sanitized += "..."

    # Remove potential secrets (simple patterns)
    sanitized = re.sub(r'password["\s:=]+\S+', 'password=***', sanitized, flags=re.I)
    sanitized = re.sub(r'api[_-]?key["\s:=]+\S+', 'api_key=***', sanitized, flags=re.I)
    sanitized = re.sub(r'token["\s:=]+\S+', 'token=***', sanitized, flags=re.I)

    return sanitized


__all__ = [
    "detect_prompt_injection",
    "get_injection_category",
    "sanitize_for_logging",
    "OVERRIDE_PATTERNS",
    "PERSONA_PATTERNS",
    "LEAKING_PATTERNS",
    "JAILBREAK_PATTERNS",
    "CODE_INJECTION_PATTERNS",
    "SPANISH_INJECTION_PATTERNS",
]
