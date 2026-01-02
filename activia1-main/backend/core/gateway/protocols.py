"""
Gateway Protocol Interfaces - Type definitions for dependency injection.

Cortez42: Extracted from ai_gateway.py (1,996 lines)

These protocols define expected interfaces for repositories without
creating circular imports. They enable proper type checking while
maintaining loose coupling.
"""
from typing import Any, List, Optional, Protocol, runtime_checkable

from ...models.trace import CognitiveTrace, TraceSequence
from ...models.risk import Risk
from ...models.evaluation import EvaluationReport


@runtime_checkable
class SessionRepositoryProtocol(Protocol):
    """Protocol for session repository operations."""

    def create(self, student_id: str, activity_id: str, mode: str) -> Any:
        """Create a new session."""
        ...

    def get_by_id(self, session_id: str) -> Any:
        """Get session by ID."""
        ...

    def update(self, session_id: str, **kwargs: Any) -> Any:
        """Update session."""
        ...


@runtime_checkable
class TraceRepositoryProtocol(Protocol):
    """Protocol for trace repository operations."""

    def create(self, trace: CognitiveTrace) -> Any:
        """Create a new trace."""
        ...

    def get_by_session(self, session_id: str) -> List[CognitiveTrace]:
        """Get all traces for a session."""
        ...


@runtime_checkable
class RiskRepositoryProtocol(Protocol):
    """Protocol for risk repository operations."""

    def create(self, risk: Risk) -> Any:
        """Create a new risk."""
        ...

    def get_by_session(self, session_id: str) -> List[Risk]:
        """Get all risks for a session."""
        ...


@runtime_checkable
class EvaluationRepositoryProtocol(Protocol):
    """Protocol for evaluation repository operations."""

    def create(self, evaluation: EvaluationReport) -> Any:
        """Create a new evaluation."""
        ...

    def get_by_session(self, session_id: str) -> Optional[EvaluationReport]:
        """Get evaluation for a session."""
        ...


@runtime_checkable
class SequenceRepositoryProtocol(Protocol):
    """Protocol for trace sequence repository operations."""

    def create(self, sequence: TraceSequence) -> Any:
        """Create a new trace sequence."""
        ...

    def get(self, sequence_id: str) -> Optional[TraceSequence]:
        """Get sequence by ID."""
        ...

    def get_by_session(self, session_id: str) -> Optional[TraceSequence]:
        """Get sequence for a session."""
        ...

    def update(self, sequence: TraceSequence) -> Any:
        """Update a trace sequence."""
        ...
