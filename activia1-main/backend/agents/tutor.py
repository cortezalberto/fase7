"""
Tutor Agent - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated tutor package.
Import from here or from backend.agents.tutor - both work.

Original implementation moved to: backend/agents/tutor/agent.py
"""

# Re-export everything from the new location
from .tutor import (
    TutorCognitivoAgent,
    TutorMode,
    HelpLevel,
)

# Also re-export common types for backward compatibility
from .tutor.rules import (
    TutorRule,
    InterventionType,
    CognitiveScaffoldingLevel,
)
from .tutor.governance import SemaforoState, PromptIntent

__all__ = [
    "TutorCognitivoAgent",
    "TutorMode",
    "HelpLevel",
    "TutorRule",
    "InterventionType",
    "CognitiveScaffoldingLevel",
    "SemaforoState",
    "PromptIntent",
]
