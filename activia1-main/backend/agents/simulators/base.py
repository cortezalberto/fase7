"""
Base Simulator - Abstract base class for professional simulators.

Cortez42: Extracted from monolithic simulators.py (1,638 lines)

Provides:
- SimuladorType: Enum of all simulator types
- BaseSimulator: Abstract base class with common functionality
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from enum import Enum
import logging
import time

# FIX Cortez73 (MED-004): Use centralized prompt injection detection
from ...utils.prompt_security import detect_prompt_injection
# FIX Cortez75: Load prompts from external files
from ...prompts.prompt_loader import get_simulator_config

logger = logging.getLogger(__name__)


class SimuladorType(str, Enum):
    """
    Tipos de simuladores profesionales

    V1 (Original - 6 tipos):
    - PRODUCT_OWNER, SCRUM_MASTER, TECH_INTERVIEWER, INCIDENT_RESPONDER, CLIENT, DEVSECOPS

    V2 (Enhanced - Sprint 6 - 5 tipos adicionales):
    - SENIOR_DEV, QA_ENGINEER, SECURITY_AUDITOR, TECH_LEAD, DEMANDING_CLIENT
    """
    # V1 - Original simulators
    PRODUCT_OWNER = "product_owner"  # PO-IA
    SCRUM_MASTER = "scrum_master"  # SM-IA
    TECH_INTERVIEWER = "tech_interviewer"  # IT-IA
    INCIDENT_RESPONDER = "incident_responder"  # IR-IA
    CLIENT = "client"  # CX-IA
    DEVSECOPS = "devsecops"  # DSO-IA

    # V2 - Enhanced simulators (Sprint 6)
    SENIOR_DEV = "senior_dev"  # SD-IA - Senior Developer
    QA_ENGINEER = "qa_engineer"  # QA-IA - QA Engineer
    SECURITY_AUDITOR = "security_auditor"  # SA-IA - Security Auditor
    TECH_LEAD = "tech_lead"  # TL-IA - Tech Lead
    DEMANDING_CLIENT = "demanding_client"  # DC-IA - Demanding Client (harder version)


class BaseSimulator(ABC):
    """
    Abstract base class for all professional simulators.

    Provides common functionality:
    - LLM response generation
    - Competency analysis
    - Conversation history loading
    - Error handling
    """

    # Class-level attributes that subclasses must define
    ROLE_NAME: str = "Unknown"
    SYSTEM_PROMPT: str = ""
    COMPETENCIES: List[str] = []
    EXPECTS: List[str] = []

    def __init__(
        self,
        llm_provider=None,
        trace_repo=None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm_provider = llm_provider
        self.trace_repo = trace_repo
        self.config = config or {}
        self.flow_id = self.config.get("flow_id")

        # FIX Cortez75: Try to load prompts from external config files
        self._load_external_config()

    @abstractmethod
    async def interact(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle student interaction. Must be implemented by subclasses.

        Args:
            student_input: Student's prompt
            context: Additional conversation context
            session_id: Session ID for conversation history

        Returns:
            Dict with message, role, expects, metadata
        """
        pass

    @abstractmethod
    def get_fallback_response(self) -> Dict[str, Any]:
        """
        Return fallback response when LLM is unavailable.
        Must be implemented by subclasses.
        """
        pass

    def _load_external_config(self) -> None:
        """
        FIX Cortez75: Load prompts and config from external .md files.

        Tries to load configuration from /prompts/simulator_{type}_config.md.
        Falls back to class-level constants if file not found.
        """
        # Derive simulator type from class name
        class_name = self.__class__.__name__
        # ProductOwnerSimulator -> product_owner
        simulator_type = ""
        for i, char in enumerate(class_name.replace("Simulator", "")):
            if char.isupper() and i > 0:
                simulator_type += "_"
            simulator_type += char.lower()

        try:
            config = get_simulator_config(simulator_type)
            if config:
                # Override class attributes with external config
                if config.get("system_prompt"):
                    self.SYSTEM_PROMPT = config["system_prompt"]
                if config.get("competencies"):
                    self.COMPETENCIES = config["competencies"]
                if config.get("expects"):
                    self.EXPECTS = config["expects"]
                if config.get("fallback_message"):
                    self._external_fallback = config["fallback_message"]
                logger.debug(
                    "Loaded external config for simulator: %s",
                    simulator_type
                )
        except Exception as e:
            # Log but don't fail - use class-level defaults
            logger.debug(
                "Using class-level config for %s: %s",
                simulator_type, e
            )

    async def _generate_llm_response(
        self,
        student_input: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        role_override: Optional[str] = None,
        system_prompt_override: Optional[str] = None,
        competencies_override: Optional[List[str]] = None,
        expects_override: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate dynamic response using LLM provider.

        Supports conversation memory via session_id.
        """
        role = role_override or self.ROLE_NAME
        system_prompt = system_prompt_override or self.SYSTEM_PROMPT
        competencies = competencies_override or self.COMPETENCIES
        expects = expects_override or self.EXPECTS

        try:
            from ...llm.base import LLMMessage, LLMRole

            # Build context string
            context_str = ""
            if context and isinstance(context, dict):
                try:
                    context_str = f"\n\nContexto adicional:\n{context}"
                except Exception as e:
                    logger.warning("Error building context string: %s", e)
                    context_str = ""

            # Build messages list
            messages = [
                LLMMessage(
                    role=LLMRole.SYSTEM,
                    content=f"{system_prompt}{context_str}"
                )
            ]

            # Load conversation history if available
            conversation_history = []
            if session_id and self.trace_repo:
                try:
                    conversation_history = self._load_conversation_history(session_id)
                    messages.extend(conversation_history)
                    logger.info(
                        "Loaded %d messages from conversation history for role %s",
                        len(conversation_history), role,
                        extra={"session_id": session_id, "role": role}
                    )
                except Exception as e:
                    logger.warning(
                        "Error loading conversation history for session %s: %s: %s",
                        session_id, type(e).__name__, e
                    )

            # Add current student input
            messages.append(
                LLMMessage(role=LLMRole.USER, content=student_input)
            )

            # Generate LLM response
            logger.info(
                "Simulator sending messages to LLM",
                extra={
                    "flow_id": self.flow_id,
                    "role": role,
                    "session_id": session_id,
                    "message_count": len(messages),
                },
            )

            import os
            simulator_temperature = float(os.getenv("SIMULATOR_TEMPERATURE", "0.7"))
            simulator_max_tokens = int(os.getenv("SIMULATOR_MAX_TOKENS", "300"))
            llm_started_at = time.perf_counter()

            response = await self.llm_provider.generate(
                messages=messages,
                temperature=simulator_temperature,
                max_tokens=simulator_max_tokens,
                is_code_analysis=False  # Simulators use Flash
            )

            logger.info(
                "Simulator received LLM response",
                extra={
                    "flow_id": self.flow_id,
                    "role": role,
                    "session_id": session_id,
                    "duration_ms": round((time.perf_counter() - llm_started_at) * 1000, 2),
                    "model": getattr(response, "model", None),
                    "total_tokens": (getattr(response, "usage", {}) or {}).get("total_tokens"),
                },
            )

            # Analyze competencies
            competency_scores = {}
            try:
                competency_scores = self._analyze_competencies(
                    student_input, response.content, competencies
                )
            except Exception as e:
                logger.warning(
                    "Error analyzing competencies for role %s: %s: %s",
                    role, type(e).__name__, e
                )

            # Build final response
            role_normalized = role.lower().replace(" ", "_")
            tokens_used = 0
            model_name = "unknown"

            if hasattr(response, 'usage') and isinstance(response.usage, dict):
                tokens_used = response.usage.get("total_tokens", 0)
            if hasattr(response, 'model'):
                model_name = response.model

            return {
                "message": response.content if hasattr(response, 'content') else str(response),
                "role": role_normalized,
                "expects": expects,
                "metadata": {
                    "competencies_evaluated": competencies,
                    "competency_scores": competency_scores,
                    "llm_model": model_name,
                    "tokens_used": tokens_used,
                    "conversation_history_length": len(conversation_history)
                }
            }

        except ValueError as ve:
            logger.error(
                "Validation error in _generate_llm_response for role %s: %s",
                role, ve, exc_info=True
            )
            return self._error_response(role, expects, competencies, "validation_error", str(ve))

        except RuntimeError as re:
            logger.error(
                "Runtime error in _generate_llm_response for role %s: %s",
                role, re, exc_info=True
            )
            return self._error_response(role, expects, competencies, "runtime_error", str(re))

        except Exception as e:
            logger.error(
                "Critical error in _generate_llm_response for role %s: %s: %s",
                role, type(e).__name__, e, exc_info=True
            )
            return self._error_response(role, expects, competencies, "critical_error", str(e))

    def _error_response(
        self,
        role: str,
        expects: List[str],
        competencies: List[str],
        error_type: str,
        error_message: str
    ) -> Dict[str, Any]:
        """Generate error response."""
        return {
            "message": f"[{role}] Ha ocurrido un error. Por favor, reformula tu consulta.",
            "role": role.lower().replace(" ", "_"),
            "expects": expects,
            "metadata": {
                "competencies_evaluated": competencies,
                "error": error_type,
                "error_message": error_message
            }
        }

    def _analyze_competencies(
        self,
        student_input: str,
        simulator_response: str,
        competencies: List[str]
    ) -> Dict[str, float]:
        """
        Analyze transversal competencies in the interaction.

        Evaluates each competency on 0.0-1.0 scale based on:
        - Communication clarity
        - Technical depth
        - Reasoning structure
        - Decision justification
        """
        scores = {}

        # Simple heuristics (in production, use LLM for sophisticated analysis)
        input_length = len(student_input.split())
        has_technical_terms = any(term in student_input.lower() for term in [
            "complejidad", "algoritmo", "estructura", "patron", "arquitectura",
            "performance", "escalabilidad", "mantenibilidad", "testing", "refactor"
        ])
        has_questions = "?" in student_input
        has_structure = any(marker in student_input for marker in ["1.", "2.", "-", "•"])

        for competency in competencies:
            score = 0.5  # Base score

            # Adjustments per competency
            if competency in ["comunicacion_tecnica", "comunicacion"]:
                if input_length > 30:
                    score += 0.2
                if has_technical_terms:
                    score += 0.2
                if has_structure:
                    score += 0.1

            elif competency in ["analisis_algoritmico", "dominio_conceptual"]:
                if has_technical_terms:
                    score += 0.3
                if input_length > 50:
                    score += 0.2

            elif competency in ["elicitacion_requisitos"]:
                if has_questions:
                    score += 0.3
                if input_length > 20:
                    score += 0.2

            elif competency in ["gestion_tiempo", "priorizacion"]:
                priority_terms = ["urgente", "critico", "primero", "luego", "despues"]
                if any(term in student_input.lower() for term in priority_terms):
                    score += 0.3

            # Cap score at 1.0
            scores[competency] = min(score, 1.0)

        return scores

    def _load_conversation_history(self, session_id: str) -> List:
        """
        Load conversation history from session as LLM messages.

        Retrieves all traces from the session and converts them to the format
        expected by the LLM provider.
        """
        if self.trace_repo is None:
            logger.warning("No trace repository available for conversation history")
            return []

        try:
            from ...llm.base import LLMMessage, LLMRole
            from ...models.trace import InteractionType

            # Retrieve all traces for this session
            db_traces = self.trace_repo.get_by_session(session_id)

            messages = []
            for trace in db_traces:
                # Add user message (STUDENT_PROMPT)
                if trace.interaction_type == InteractionType.STUDENT_PROMPT.value and trace.content:
                    messages.append(
                        LLMMessage(role=LLMRole.USER, content=trace.content)
                    )

                # Add assistant response (AI_RESPONSE or TUTOR_INTERVENTION)
                elif trace.interaction_type in [
                    InteractionType.AI_RESPONSE.value,
                    InteractionType.TUTOR_INTERVENTION.value
                ] and trace.content:
                    messages.append(
                        LLMMessage(role=LLMRole.ASSISTANT, content=trace.content)
                    )

            logger.info(
                "Loaded conversation history: %d messages",
                len(messages),
                extra={"session_id": session_id}
            )
            return messages

        except Exception as e:
            logger.error(
                "Error loading conversation history: %s",
                e,
                exc_info=True,
                extra={"session_id": session_id}
            )
            return []

    def validate_input(self, student_input: str) -> Optional[Dict[str, Any]]:
        """
        Validate student input. Returns error response if invalid, None if valid.
        """
        if not student_input or not isinstance(student_input, str):
            logger.error("Invalid student_input: %s", student_input)
            return {
                "message": "Por favor, ingresa un mensaje valido para continuar la simulacion.",
                "role": self.ROLE_NAME.lower().replace(" ", "_"),
                "expects": [],
                "metadata": {"error": "invalid_input"}
            }

        if student_input.strip() == "":
            logger.warning("Empty student_input for simulator %s", self.ROLE_NAME)
            return {
                "message": "Esperaba una respuesta de tu parte. Podrias compartir tu opinion o propuesta?",
                "role": self.ROLE_NAME.lower().replace(" ", "_"),
                "expects": ["respuesta"],
                "metadata": {"warning": "empty_input"}
            }

        # FIX Cortez69/73 (CRIT-AGENT-004/MED-004): Check for prompt injection (centralized)
        if detect_prompt_injection(student_input):
            logger.warning(
                "Prompt injection detected in simulator %s",
                self.ROLE_NAME,
                extra={"input_preview": student_input[:100]}
            )
            return {
                "message": "Tu mensaje contiene patrones no permitidos. Por favor, reformula tu consulta de manera profesional.",
                "role": self.ROLE_NAME.lower().replace(" ", "_"),
                "expects": ["reformulacion"],
                "metadata": {"error": "prompt_injection_detected"}
            }

        return None

    # FIX Cortez73 (MED-004): Removed local _detect_prompt_injection method.
    # Now using centralized detect_prompt_injection from utils.prompt_security
