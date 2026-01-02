"""
Factory for Tutor Mode Strategies.

Cortez46: Extracted from tutor.py (1,422 lines)

Provides centralized creation and caching of tutor mode strategies.
"""
from typing import Dict, Optional
import logging

from .base import TutorModeStrategy, TutorMode
from .socratic import SocraticStrategy
from .explicative import ExplicativeStrategy
from .guided import GuidedStrategy
from .metacognitive import MetacognitiveStrategy, ClarificationStrategy

logger = logging.getLogger(__name__)


class TutorModeFactory:
    """
    Factory for creating and caching tutor mode strategies.

    Implements a simple registry pattern for mode strategies.
    Strategies are cached as singletons since they're stateless.
    """

    _strategies: Dict[TutorMode, TutorModeStrategy] = {}
    _clarification_strategy: Optional[ClarificationStrategy] = None

    @classmethod
    def get_strategy(cls, mode: TutorMode) -> TutorModeStrategy:
        """
        Get or create a strategy for the given mode.

        Args:
            mode: TutorMode enum value

        Returns:
            TutorModeStrategy instance for the mode

        Raises:
            ValueError: If mode is not recognized
        """
        if mode not in cls._strategies:
            cls._strategies[mode] = cls._create_strategy(mode)
            logger.debug("Created strategy for mode: %s", mode.value)

        return cls._strategies[mode]

    @classmethod
    def get_clarification_strategy(cls) -> ClarificationStrategy:
        """
        Get the clarification request strategy.

        Returns:
            ClarificationStrategy instance
        """
        if cls._clarification_strategy is None:
            cls._clarification_strategy = ClarificationStrategy()
            logger.debug("Created clarification strategy")

        return cls._clarification_strategy

    @classmethod
    def _create_strategy(cls, mode: TutorMode) -> TutorModeStrategy:
        """
        Create a new strategy instance for the given mode.

        Args:
            mode: TutorMode enum value

        Returns:
            TutorModeStrategy instance

        Raises:
            ValueError: If mode is not recognized
        """
        strategy_map = {
            TutorMode.SOCRATICO: SocraticStrategy,
            TutorMode.EXPLICATIVO: ExplicativeStrategy,
            TutorMode.GUIADO: GuidedStrategy,
            TutorMode.METACOGNITIVO: MetacognitiveStrategy,
        }

        strategy_class = strategy_map.get(mode)
        if strategy_class is None:
            raise ValueError(f"Unknown tutor mode: {mode}")

        return strategy_class()

    @classmethod
    def get_strategy_from_response_type(
        cls,
        response_type: str
    ) -> TutorModeStrategy:
        """
        Get strategy based on response_type string from legacy code.

        Maps old response_type strings to new mode strategies.

        Args:
            response_type: Legacy response type string

        Returns:
            TutorModeStrategy instance
        """
        response_type_map = {
            "socratic_questioning": TutorMode.SOCRATICO,
            "conceptual_explanation": TutorMode.EXPLICATIVO,
            "guided_hints": TutorMode.GUIADO,
            "metacognitive_reflection": TutorMode.METACOGNITIVO,
        }

        mode = response_type_map.get(response_type)
        if mode is None:
            logger.warning(
                "Unknown response_type '%s', using socratic as fallback",
                response_type
            )
            mode = TutorMode.SOCRATICO

        return cls.get_strategy(mode)

    @classmethod
    def reset(cls) -> None:
        """
        Reset the factory, clearing all cached strategies.

        Useful for testing or when configuration changes.
        """
        cls._strategies.clear()
        cls._clarification_strategy = None
        logger.debug("TutorModeFactory reset")

    @classmethod
    def available_modes(cls) -> list:
        """
        Get list of available tutor modes.

        Returns:
            List of TutorMode enum values
        """
        return list(TutorMode)
