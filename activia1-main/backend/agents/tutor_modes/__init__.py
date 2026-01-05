"""
Tutor Mode Strategies Package - Strategy Pattern for T-IA-Cog modes.

Cortez46: Extracted from tutor.py (1,422 lines) using Strategy Pattern.
Cortez76: Removed TrainingHintsStrategy (Entrenador Digital removed).

This package provides modular tutor mode implementations:
- base.py: Abstract TutorModeStrategy base class
- socratic.py: Socratic questioning mode (TutorMode.SOCRATICO)
- explicative.py: Conceptual explanation mode (TutorMode.EXPLICATIVO)
- guided.py: Guided hints with scaffolding (TutorMode.GUIADO)
- metacognitive.py: Metacognitive reflection mode (TutorMode.METACOGNITIVO)

Usage:
    from backend.agents.tutor_modes import (
        TutorModeStrategy,
        SocraticStrategy,
        ExplicativeStrategy,
        GuidedStrategy,
        MetacognitiveStrategy,
        TutorModeFactory,
    )
"""

from .base import TutorModeStrategy, TutorModeContext
from .socratic import SocraticStrategy
from .explicative import ExplicativeStrategy
from .guided import GuidedStrategy
from .metacognitive import MetacognitiveStrategy
from .factory import TutorModeFactory

__all__ = [
    # Base
    "TutorModeStrategy",
    "TutorModeContext",
    # Strategies
    "SocraticStrategy",
    "ExplicativeStrategy",
    "GuidedStrategy",
    "MetacognitiveStrategy",
    # Factory
    "TutorModeFactory",
]
