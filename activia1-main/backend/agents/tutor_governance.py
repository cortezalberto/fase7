"""
Tutor Governance - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated tutor package.
Import from here or from backend.agents.tutor.governance - both work.

Original implementation moved to: backend/agents/tutor/governance.py
"""

# Re-export everything from the new location
from .tutor.governance import (
    SemaforoState,
    PromptIntent,
    StudentContextAnalysis,
    TutorGovernanceEngine,
)

__all__ = [
    "SemaforoState",
    "PromptIntent",
    "StudentContextAnalysis",
    "TutorGovernanceEngine",
]
