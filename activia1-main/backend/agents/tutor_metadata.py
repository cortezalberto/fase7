"""
Tutor Metadata - Backward Compatibility Wrapper

Cortez66: This file re-exports from the consolidated tutor package.
Import from here or from backend.agents.tutor.metadata - both work.

Original implementation moved to: backend/agents/tutor/metadata.py
"""

# Re-export everything from the new location
from .tutor.metadata import (
    InterventionEffectiveness,
    StudentCognitiveEvent,
    TutorInterventionMetadata,
    TutorMetadataTracker,
)

__all__ = [
    "InterventionEffectiveness",
    "StudentCognitiveEvent",
    "TutorInterventionMetadata",
    "TutorMetadataTracker",
]
