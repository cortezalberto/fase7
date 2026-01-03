"""
Tutor Package - T-IA-Cog Cognitive Tutor Agent

Cortez66: Consolidated from scattered tutor_*.py files in agents/

This package contains the cognitive tutor agent components:
- agent.py: TutorCognitivoAgent main class
- rules.py: TutorRulesEngine and pedagogical rules
- governance.py: TutorGovernanceEngine with semaphore system
- metadata.py: TutorMetadataTracker for N4 traceability
- prompts.py: TutorSystemPrompts for LLM interactions

Related package: backend/agents/tutor_modes/ contains the Strategy Pattern
implementations for different tutor modes (Socratic, Explicative, Guided, etc.)

Usage:
    from backend.agents.tutor import (
        TutorCognitivoAgent,
        TutorMode,
        HelpLevel,
        TutorRulesEngine,
        TutorGovernanceEngine,
    )
"""

# Main agent
from .agent import (
    TutorCognitivoAgent,
    TutorMode,
    HelpLevel,
)

# Rules engine
from .rules import (
    TutorRulesEngine,
    TutorRule,
    InterventionType,
    CognitiveScaffoldingLevel,
)

# Governance engine
from .governance import (
    TutorGovernanceEngine,
    SemaforoState,
    PromptIntent,
    StudentContextAnalysis,
)

# Metadata tracker
from .metadata import (
    TutorMetadataTracker,
    TutorInterventionMetadata,
    InterventionEffectiveness,
    StudentCognitiveEvent,
)

# System prompts
from .prompts import TutorSystemPrompts

__all__ = [
    # Agent
    "TutorCognitivoAgent",
    "TutorMode",
    "HelpLevel",
    # Rules
    "TutorRulesEngine",
    "TutorRule",
    "InterventionType",
    "CognitiveScaffoldingLevel",
    # Governance
    "TutorGovernanceEngine",
    "SemaforoState",
    "PromptIntent",
    "StudentContextAnalysis",
    # Metadata
    "TutorMetadataTracker",
    "TutorInterventionMetadata",
    "InterventionEffectiveness",
    "StudentCognitiveEvent",
    # Prompts
    "TutorSystemPrompts",
]
