"""
Tutor Prompts - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated tutor package.
Import from here or from backend.agents.tutor.prompts - both work.

Original implementation moved to: backend/agents/tutor/prompts.py
"""

# Re-export everything from the new location
from .tutor.prompts import TutorSystemPrompts

__all__ = [
    "TutorSystemPrompts",
]
