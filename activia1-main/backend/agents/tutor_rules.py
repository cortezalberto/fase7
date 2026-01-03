"""
Tutor Rules - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated tutor package.
Import from here or from backend.agents.tutor.rules - both work.

Original implementation moved to: backend/agents/tutor/rules.py
"""

# Re-export everything from the new location
from .tutor.rules import (
    TutorRule,
    InterventionType,
    CognitiveScaffoldingLevel,
    TutorRulesEngine,
)

__all__ = [
    "TutorRule",
    "InterventionType",
    "CognitiveScaffoldingLevel",
    "TutorRulesEngine",
]
