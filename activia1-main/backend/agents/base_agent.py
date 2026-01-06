"""
Base Agent - Protocol and Mixin for AI Agents.

Cortez89: Architecture improvement - centralized agent contracts and utilities.
Cortez92: Added typed config dataclasses for agent configuration (MED-005).

Provides:
- BaseAgentProtocol: Interface contract for all AI agents (P2)
- LLMGenerationMixin: Reusable LLM generation with timeout handling (P1)
- AgentResponseBuilder: Standardized response building
- Typed config dataclasses for agent configuration (MED-005)

Benefits:
- Consistent interface across all agents (Protocol-based typing)
- Eliminates ~200 lines of duplicated LLM timeout code
- Type-safe with IDE autocompletion support
- Centralized error handling and logging
- Validated configuration with dataclasses (MED-005)
"""
import asyncio
import logging
import time
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, Dict, Any, Optional, List, runtime_checkable

from ..llm.base import LLMMessage, LLMRole, LLMResponse
from ..core.constants import (
    LLM_TIMEOUT_SECONDS,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_TOKENS,
    RAG_DEFAULT_MAX_DOCUMENTS,
    RAG_DEFAULT_MIN_CONFIDENCE,
)

logger = logging.getLogger(__name__)


# =============================================================================
# MED-005: Typed Configuration Dataclasses
# =============================================================================

@dataclass
class LLMConfig:
    """
    Cortez92 MED-005: Typed configuration for LLM generation.

    Replaces Dict[str, Any] with validated, type-safe configuration.
    Provides sensible defaults from centralized constants.

    Example:
        config = LLMConfig(temperature=0.5, max_tokens=500)
        response = await agent._generate_with_timeout(messages, **config.to_dict())
    """
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout: float = LLM_TIMEOUT_SECONDS
    is_code_analysis: bool = False

    def __post_init__(self):
        """Validate configuration values."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"temperature must be between 0.0 and 2.0, got {self.temperature}")
        if self.max_tokens < 1:
            raise ValueError(f"max_tokens must be positive, got {self.max_tokens}")
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for passing to LLM methods."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "is_code_analysis": self.is_code_analysis,
        }


@dataclass
class RAGConfig:
    """
    Cortez92 MED-005: Typed configuration for RAG agent.

    Replaces Dict[str, Any] with validated, type-safe configuration.
    """
    max_documents: int = RAG_DEFAULT_MAX_DOCUMENTS
    min_confidence: float = RAG_DEFAULT_MIN_CONFIDENCE
    context_template: Optional[str] = None

    def __post_init__(self):
        """Validate configuration values."""
        if self.max_documents < 1:
            raise ValueError(f"max_documents must be positive, got {self.max_documents}")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError(f"min_confidence must be between 0.0 and 1.0, got {self.min_confidence}")


@dataclass
class AgentConfig:
    """
    Cortez92 MED-005: Base typed configuration for all agents.

    Provides common configuration fields that all agents share.
    Subclass for agent-specific configuration.

    Example:
        @dataclass
        class TutorConfig(AgentConfig):
            mode: str = "socratic"
            max_hints: int = 3

        config = TutorConfig(llm=LLMConfig(temperature=0.5))
        tutor = TutorAgent(llm_provider, config)
    """
    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: Optional[RAGConfig] = None
    enable_logging: bool = True
    fallback_message: str = "Lo siento, no puedo procesar tu solicitud en este momento."

    @classmethod
    def from_dict(cls, config_dict: Optional[Dict[str, Any]] = None) -> "AgentConfig":
        """
        Create AgentConfig from dictionary (for backward compatibility).

        Args:
            config_dict: Optional dictionary with configuration values

        Returns:
            AgentConfig instance with values from dict or defaults
        """
        if not config_dict:
            return cls()

        llm_dict = config_dict.get("llm", {})
        rag_dict = config_dict.get("rag")

        llm_config = LLMConfig(
            temperature=llm_dict.get("temperature", DEFAULT_TEMPERATURE),
            max_tokens=llm_dict.get("max_tokens", DEFAULT_MAX_TOKENS),
            timeout=llm_dict.get("timeout", LLM_TIMEOUT_SECONDS),
            is_code_analysis=llm_dict.get("is_code_analysis", False),
        )

        rag_config = None
        if rag_dict:
            rag_config = RAGConfig(
                max_documents=rag_dict.get("max_documents", RAG_DEFAULT_MAX_DOCUMENTS),
                min_confidence=rag_dict.get("min_confidence", RAG_DEFAULT_MIN_CONFIDENCE),
                context_template=rag_dict.get("context_template"),
            )

        return cls(
            llm=llm_config,
            rag=rag_config,
            enable_logging=config_dict.get("enable_logging", True),
            fallback_message=config_dict.get(
                "fallback_message",
                "Lo siento, no puedo procesar tu solicitud en este momento."
            ),
        )


# =============================================================================
# P2: BaseAgent Protocol - Interface Contract
# =============================================================================

@runtime_checkable
class BaseAgentProtocol(Protocol):
    """
    Cortez89: Protocol defining the contract for all AI agents.

    All agents should implement this interface for consistency.
    Using Protocol (structural subtyping) instead of ABC allows
    for gradual adoption without requiring inheritance changes.

    Benefits:
    - Type checking with isinstance() via @runtime_checkable
    - IDE autocompletion for agent methods
    - Documentation of expected agent interface
    - No inheritance required (duck typing compatible)

    Example usage:
        def process_with_agent(agent: BaseAgentProtocol, input: str):
            # Works with any agent implementing the protocol
            result = await agent.process(input)
            return result

        # Type checking
        if isinstance(my_agent, BaseAgentProtocol):
            # Agent implements required methods
            pass
    """

    @property
    def llm_provider(self) -> Any:
        """LLM provider instance for generating responses."""
        ...

    async def process(
        self,
        input_data: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main processing method for agent interactions.

        Args:
            input_data: User input or query to process
            context: Additional context (student profile, activity, etc.)
            session_id: Session identifier for conversation tracking

        Returns:
            Dictionary with:
            - message: Agent's response text
            - metadata: Processing metadata (model, tokens, timing)
            - Additional agent-specific fields
        """
        ...

    def get_fallback_response(self) -> Dict[str, Any]:
        """
        Return fallback response when LLM is unavailable.

        Used when:
        - LLM provider is not configured
        - LLM call times out
        - LLM returns an error

        Returns:
            Dictionary with safe fallback message and metadata
        """
        ...


# =============================================================================
# P1: LLM Generation Mixin - Reusable LLM Utilities
# =============================================================================

class LLMGenerationMixin:
    """
    Cortez89: Mixin providing reusable LLM generation utilities.

    Consolidates duplicated LLM generation code from:
    - backend/agents/simulators/base.py
    - backend/agents/tutor/agent.py
    - backend/agents/risk_analyst.py
    - backend/agents/evaluator.py

    Benefits:
    - Single implementation of timeout handling
    - Consistent error handling and logging
    - Centralized metric collection
    - Easy to test and maintain

    Usage:
        class MyAgent(LLMGenerationMixin):
            def __init__(self, llm_provider):
                self.llm_provider = llm_provider

            async def process(self, input_data: str):
                messages = [LLMMessage(role=LLMRole.USER, content=input_data)]
                response = await self._generate_with_timeout(messages)
                if response is None:
                    return self.get_fallback_response()
                return {"message": response.content}
    """

    # Subclasses must set this attribute
    llm_provider: Any

    async def _generate_with_timeout(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: int = 300,
        timeout: Optional[float] = None,
        is_code_analysis: bool = False,
        context_label: str = "agent"
    ) -> Optional[LLMResponse]:
        """
        Generate LLM response with timeout protection.

        Args:
            messages: List of LLM messages (system, user, assistant)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum response tokens
            timeout: Custom timeout (defaults to LLM_TIMEOUT_SECONDS)
            is_code_analysis: If True, uses code-optimized model
            context_label: Label for logging (e.g., "tutor", "simulator")

        Returns:
            LLMResponse if successful, None if timeout or error

        Note:
            On timeout or error, caller should use get_fallback_response()
        """
        if not self.llm_provider:
            logger.warning(
                "No LLM provider available for %s - using fallback",
                context_label
            )
            return None

        effective_timeout = timeout or LLM_TIMEOUT_SECONDS
        start_time = time.perf_counter()

        try:
            response = await asyncio.wait_for(
                self.llm_provider.generate(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    is_code_analysis=is_code_analysis
                ),
                timeout=effective_timeout
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "%s LLM response received",
                context_label.capitalize(),
                extra={
                    "context": context_label,
                    "duration_ms": duration_ms,
                    "model": getattr(response, "model", None),
                    "total_tokens": (getattr(response, "usage", {}) or {}).get("total_tokens"),
                }
            )
            return response

        except asyncio.TimeoutError:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "%s LLM timeout after %.1f seconds (%.2f ms)",
                context_label.capitalize(),
                effective_timeout,
                duration_ms,
                extra={"context": context_label, "timeout": effective_timeout}
            )
            return None

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                "%s LLM error: %s - %s (%.2f ms)",
                context_label.capitalize(),
                type(e).__name__,
                str(e),
                duration_ms,
                exc_info=True,
                extra={"context": context_label}
            )
            return None

    async def _generate_with_retry(
        self,
        messages: List[LLMMessage],
        max_retries: int = 2,
        retry_delay: float = 1.0,
        **kwargs
    ) -> Optional[LLMResponse]:
        """
        Generate LLM response with retry on transient failures.

        Args:
            messages: List of LLM messages
            max_retries: Maximum retry attempts (default: 2)
            retry_delay: Delay between retries in seconds (default: 1.0)
            **kwargs: Additional arguments for _generate_with_timeout

        Returns:
            LLMResponse if successful, None if all retries fail
        """
        last_error = None

        for attempt in range(max_retries + 1):
            response = await self._generate_with_timeout(messages, **kwargs)
            if response is not None:
                return response

            if attempt < max_retries:
                logger.warning(
                    "LLM generation attempt %d/%d failed, retrying in %.1fs",
                    attempt + 1,
                    max_retries + 1,
                    retry_delay
                )
                await asyncio.sleep(retry_delay)
                # Exponential backoff
                retry_delay *= 2

        logger.error(
            "LLM generation failed after %d attempts",
            max_retries + 1
        )
        return None

    def _build_system_message(
        self,
        system_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> LLMMessage:
        """
        Build system message with optional context injection.

        Args:
            system_prompt: Base system prompt
            context: Additional context to append

        Returns:
            LLMMessage with role=SYSTEM
        """
        content = system_prompt

        if context:
            context_str = "\n\nContexto adicional:\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            content += context_str

        return LLMMessage(role=LLMRole.SYSTEM, content=content)

    def _build_conversation_messages(
        self,
        system_prompt: str,
        user_input: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[LLMMessage]:
        """
        Build complete message list for LLM conversation.

        Args:
            system_prompt: System prompt defining agent behavior
            user_input: Current user message
            conversation_history: Previous messages [{role, content}]
            context: Additional context for system message

        Returns:
            List of LLMMessage ready for LLM.generate()
        """
        messages = [self._build_system_message(system_prompt, context)]

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                role = LLMRole.USER if msg.get("role") == "user" else LLMRole.ASSISTANT
                messages.append(LLMMessage(role=role, content=msg.get("content", "")))

        # Add current user input
        messages.append(LLMMessage(role=LLMRole.USER, content=user_input))

        return messages


# =============================================================================
# Response Builder - Standardized Response Format
# =============================================================================

class AgentResponseBuilder:
    """
    Cortez89: Helper for building standardized agent responses.

    Ensures consistent response format across all agents.
    """

    @staticmethod
    def success(
        message: str,
        role: str = "agent",
        metadata: Optional[Dict[str, Any]] = None,
        **extra_fields
    ) -> Dict[str, Any]:
        """
        Build successful response.

        Args:
            message: Agent's response message
            role: Agent role identifier
            metadata: Processing metadata
            **extra_fields: Additional fields to include

        Returns:
            Standardized success response dict
        """
        response = {
            "message": message,
            "role": role,
            "status": "success",
            "metadata": metadata or {}
        }
        response.update(extra_fields)
        return response

    @staticmethod
    def error(
        message: str,
        error_type: str,
        role: str = "agent",
        error_details: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build error response.

        Args:
            message: User-facing error message
            error_type: Error classification (e.g., "timeout", "validation")
            role: Agent role identifier
            error_details: Internal error details (logged, not shown to user)

        Returns:
            Standardized error response dict
        """
        if error_details:
            logger.error(
                "Agent error [%s]: %s - %s",
                role,
                error_type,
                error_details
            )

        return {
            "message": message,
            "role": role,
            "status": "error",
            "metadata": {
                "error": error_type,
            }
        }

    @staticmethod
    def fallback(
        message: str,
        role: str = "agent",
        reason: str = "llm_unavailable"
    ) -> Dict[str, Any]:
        """
        Build fallback response when LLM is unavailable.

        Args:
            message: Fallback message to user
            role: Agent role identifier
            reason: Reason for fallback

        Returns:
            Standardized fallback response dict
        """
        return {
            "message": message,
            "role": role,
            "status": "fallback",
            "metadata": {
                "fallback_reason": reason,
            }
        }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "BaseAgentProtocol",
    "LLMGenerationMixin",
    "AgentResponseBuilder",
    # MED-005: Typed configuration dataclasses
    "LLMConfig",
    "RAGConfig",
    "AgentConfig",
]
