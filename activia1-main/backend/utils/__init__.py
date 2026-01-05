"""
Utility modules for AI-Native MVP backend.

FIX Cortez36: Created utils package to consolidate duplicate code.
FIX Cortez73 (MED-004): Added prompt_security module for centralized injection detection.
"""
from .sandbox import execute_python_code
from .prompt_security import (
    detect_prompt_injection,
    get_injection_category,
    sanitize_for_logging,
)

__all__ = [
    "execute_python_code",
    "detect_prompt_injection",
    "get_injection_category",
    "sanitize_for_logging",
]
