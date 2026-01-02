"""
Base Strategy class for Tutor Modes.

Cortez46: Extracted from tutor.py (1,422 lines)

Defines the interface and common functionality for all tutor mode strategies.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TutorMode(str, Enum):
    """Modos de tutoria"""
    SOCRATICO = "socratico"
    EXPLICATIVO = "explicativo"
    GUIADO = "guiado"
    METACOGNITIVO = "metacognitivo"


class HelpLevel(str, Enum):
    """Niveles de ayuda"""
    MINIMO = "minimo"
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


@dataclass
class TutorModeContext:
    """
    Context object passed to strategy methods.

    Encapsulates all information needed for generating responses.
    """
    student_prompt: str
    cognitive_state: str
    strategy: Dict[str, Any]
    student_history: Optional[List[Any]] = None
    conversation_history: Optional[List[Dict[str, Any]]] = None
    student_profile: Optional[Dict[str, Any]] = None
    llm_provider: Optional[Any] = None
    prompts: Optional[Any] = None  # TutorSystemPrompts instance
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TutorResponse:
    """
    Standardized response from tutor mode strategies.
    """
    message: str
    mode: TutorMode
    pedagogical_intent: str
    requires_student_response: bool = True
    help_level: Optional[HelpLevel] = None
    questions: Optional[List[str]] = None
    hints_provided: Optional[List[Dict[str, str]]] = None
    hints_count: int = 0
    previous_hints_count: int = 0
    requires_justification: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format expected by tutor.py"""
        result = {
            "message": self.message,
            "mode": self.mode,
            "pedagogical_intent": self.pedagogical_intent,
            "requires_student_response": self.requires_student_response,
            "metadata": self.metadata,
        }

        if self.help_level:
            result["help_level"] = self.help_level
        if self.questions:
            result["questions"] = self.questions
        if self.hints_provided:
            result["hints_provided"] = self.hints_provided
            result["hints_count"] = self.hints_count
            result["previous_hints_count"] = self.previous_hints_count
        if self.requires_justification:
            result["requires_justification"] = self.requires_justification

        return result


class TutorModeStrategy(ABC):
    """
    Abstract base class for tutor mode strategies.

    Each strategy implements a specific pedagogical approach:
    - Socratic: Questioning to promote reasoning
    - Explicative: Conceptual explanations
    - Guided: Graduated hints with scaffolding
    - Metacognitive: Reflection on learning process
    """

    @property
    @abstractmethod
    def mode(self) -> TutorMode:
        """Return the TutorMode this strategy implements"""
        pass

    @property
    @abstractmethod
    def pedagogical_intent(self) -> str:
        """Return the pedagogical intent/purpose of this mode"""
        pass

    @abstractmethod
    async def generate_response(
        self,
        context: TutorModeContext,
    ) -> TutorResponse:
        """
        Generate a response using this mode's pedagogical approach.

        Args:
            context: TutorModeContext with all necessary information

        Returns:
            TutorResponse with message and metadata
        """
        pass

    async def generate_with_llm(
        self,
        context: TutorModeContext,
        system_prompt: str,
    ) -> Optional[str]:
        """
        Generate response content using LLM if available.

        Args:
            context: TutorModeContext with llm_provider
            system_prompt: System prompt for LLM

        Returns:
            LLM response content or None if unavailable/failed
        """
        if not context.llm_provider:
            logger.debug("No LLM provider available for %s mode", self.mode.value)
            return None

        try:
            from ...llm.base import LLMMessage, LLMRole

            messages = [
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(role=LLMRole.USER, content=f"Estudiante pregunta: {context.student_prompt}")
            ]

            llm_response = await context.llm_provider.generate(
                messages,
                temperature=0.7,
                max_tokens=500
            )

            response_text = (
                llm_response.content
                if hasattr(llm_response, 'content')
                else str(llm_response)
            )

            logger.info(
                "Successfully generated %s response with LLM",
                self.mode.value
            )
            return response_text

        except AttributeError as e:
            logger.error(
                "LLM attribute error in %s mode: %s: %s",
                self.mode.value, type(e).__name__, e,
                exc_info=True
            )
        except ValueError as e:
            logger.error(
                "LLM value error in %s mode: %s: %s",
                self.mode.value, type(e).__name__, e,
                exc_info=True
            )
        except Exception as e:
            logger.error(
                "LLM generation failed in %s mode: %s: %s",
                self.mode.value, type(e).__name__, e,
                exc_info=True
            )

        return None

    def get_system_prompt(
        self,
        context: TutorModeContext,
        intervention_type: Any,
    ) -> str:
        """
        Get system prompt from TutorSystemPrompts.

        Args:
            context: TutorModeContext with prompts instance
            intervention_type: InterventionType enum value

        Returns:
            System prompt string
        """
        if not context.prompts:
            logger.warning("No prompts instance available, using empty prompt")
            return ""

        from ..tutor_rules import CognitiveScaffoldingLevel
        from ..tutor_governance import SemaforoState

        student_level = context.strategy.get(
            "student_level",
            CognitiveScaffoldingLevel.INTERMEDIO
        )

        semaforo_str = context.strategy.get("semaforo_state", "verde")
        if isinstance(semaforo_str, str):
            semaforo_map = {
                "verde": SemaforoState.VERDE,
                "amarillo": SemaforoState.AMARILLO,
                "rojo": SemaforoState.ROJO
            }
            semaforo_state = semaforo_map.get(semaforo_str, SemaforoState.VERDE)
        else:
            semaforo_state = semaforo_str

        return context.prompts.get_intervention_prompt(
            intervention_type=intervention_type,
            student_level=student_level,
            semaforo_state=semaforo_state,
            context={
                "cognitive_state": context.cognitive_state,
                "help_level": context.strategy.get("help_level", "medio"),
                "prompt": context.student_prompt
            }
        )
