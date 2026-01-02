"""
Tutor Mode Strategies Package - Strategy Pattern for T-IA-Cog modes.

Cortez46: Extracted from tutor.py (1,422 lines) using Strategy Pattern.
Cortez50: Added TrainingHintsStrategy for Digital Trainer integration.

This package provides modular tutor mode implementations:
- base.py: Abstract TutorModeStrategy base class
- socratic.py: Socratic questioning mode (TutorMode.SOCRATICO)
- explicative.py: Conceptual explanation mode (TutorMode.EXPLICATIVO)
- guided.py: Guided hints with scaffolding (TutorMode.GUIADO)
- metacognitive.py: Metacognitive reflection mode (TutorMode.METACOGNITIVO)
- training_hints.py: Training-specific hints for Digital Trainer (Cortez50)

Usage:
    from backend.agents.tutor_modes import (
        TutorModeStrategy,
        SocraticStrategy,
        ExplicativeStrategy,
        GuidedStrategy,
        MetacognitiveStrategy,
        TrainingHintsStrategy,
        TutorModeFactory,
    )
"""

from .base import TutorModeStrategy, TutorModeContext
from .socratic import SocraticStrategy
from .explicative import ExplicativeStrategy
from .guided import GuidedStrategy
from .metacognitive import MetacognitiveStrategy
from .training_hints import (
    TrainingHintsStrategy,
    ExerciseContext,
    AttemptContext,
    TrainingHintRequest,
    create_training_hints_strategy,
)
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
    # Training (Cortez50)
    "TrainingHintsStrategy",
    "ExerciseContext",
    "AttemptContext",
    "TrainingHintRequest",
    "create_training_hints_strategy",
    # Factory
    "TutorModeFactory",
]
