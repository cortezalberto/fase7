"""
Trace Coordinator - N4 Traceability management for AIGateway.

Cortez66: Extracted from ai_gateway.py (2,389 lines)

This module handles:
- Trace creation and persistence
- Conversation history loading
- Student history retrieval
- Trace sequence management

All operations are STATELESS - data is persisted to PostgreSQL.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...models.trace import CognitiveTrace, TraceSequence, InteractionType, TraceLevel

if TYPE_CHECKING:
    from .protocols import TraceRepositoryProtocol, SequenceRepositoryProtocol
    from ...llm.base import LLMMessage

logger = logging.getLogger(__name__)


def _get_metrics():
    """Lazy import to avoid circular dependencies."""
    try:
        from ...api.routers.metrics import metrics
        return metrics
    except ImportError:
        return None


class TraceCoordinator:
    """
    Coordinates N4 cognitive trace operations.

    This class manages the creation, persistence, and retrieval of
    cognitive traces. It's designed to be STATELESS - all data is
    persisted to the database immediately.

    Attributes:
        trace_repo: Repository for trace operations
        sequence_repo: Repository for trace sequence operations
    """

    def __init__(
        self,
        trace_repo: Optional["TraceRepositoryProtocol"] = None,
        sequence_repo: Optional["SequenceRepositoryProtocol"] = None,
    ):
        """
        Initialize the TraceCoordinator.

        Args:
            trace_repo: Repository for trace CRUD operations
            sequence_repo: Repository for trace sequence operations
        """
        self.trace_repo = trace_repo
        self.sequence_repo = sequence_repo

    def create_trace(
        self,
        session_id: str,
        student_id: str,
        activity_id: str,
        interaction_type: InteractionType,
        content: str,
        level: TraceLevel,
        **kwargs
    ) -> CognitiveTrace:
        """
        Create a cognitive trace object (does not persist yet).

        Args:
            session_id: Session ID
            student_id: Student ID
            activity_id: Activity ID
            interaction_type: Type of interaction (STUDENT_PROMPT, AI_RESPONSE, etc.)
            content: Content of the trace
            level: N4 trace level (N1, N2, N3, N4)
            **kwargs: Additional trace fields (cognitive_state, ai_involvement, etc.)

        Returns:
            CognitiveTrace object (not persisted)
        """
        trace_id = str(uuid.uuid4())

        return CognitiveTrace(
            id=trace_id,
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            trace_level=level,
            interaction_type=interaction_type,
            content=content,
            **kwargs
        )

    def persist_trace(self, trace: CognitiveTrace) -> None:
        """
        Persist a trace to the database (STATELESS).

        Args:
            trace: CognitiveTrace object to persist

        Note:
            If trace_repo is None, this is a no-op for backward compatibility.
        """
        if self.trace_repo is not None:
            try:
                db_trace = self.trace_repo.create(trace)
                logger.debug(
                    "Trace persisted successfully",
                    extra={
                        "trace_id": db_trace.id,
                        "interaction_type": trace.interaction_type.value,
                        "session_id": trace.session_id,
                        "cognitive_state": trace.cognitive_state.value if trace.cognitive_state else None
                    }
                )
                # Record Prometheus metric for trace creation
                metrics = _get_metrics()
                if metrics:
                    metrics.record_trace_creation(
                        trace_level=trace.trace_level.value if hasattr(trace.trace_level, 'value') else str(trace.trace_level),
                        interaction_type=trace.interaction_type.value if hasattr(trace.interaction_type, 'value') else str(trace.interaction_type)
                    )
            except Exception as e:
                logger.error(
                    "Failed to persist trace",
                    extra={
                        "error": str(e),
                        "session_id": trace.session_id,
                        "interaction_type": trace.interaction_type.value
                    },
                    exc_info=True
                )
        else:
            logger.warning(
                "Trace repository is None, cannot persist trace",
                extra={
                    "session_id": trace.session_id,
                    "interaction_type": trace.interaction_type.value
                }
            )

    def load_conversation_history(
        self,
        session_id: str,
        max_messages: int = 50
    ) -> List["LLMMessage"]:
        """
        Load conversation history for a session as LLM messages.

        Retrieves the most recent traces from the session and converts them
        to the LLM message format, maintaining conversation context.

        Args:
            session_id: Session ID
            max_messages: Maximum number of messages to return (default: 50)

        Returns:
            List of LLMMessage with formatted history (last max_messages)
        """
        from ...llm.interfaces import LLMMessage, LLMRole

        if self.trace_repo is None:
            logger.warning("No trace repository available for conversation history")
            return []

        try:
            # Limit to 100 traces to prevent OOM in long sessions
            db_traces = self.trace_repo.get_by_session(session_id, limit=100)

            messages = []
            for trace in db_traces:
                # Add user message (STUDENT_PROMPT)
                if trace.interaction_type == InteractionType.STUDENT_PROMPT.value and trace.content:
                    messages.append(
                        LLMMessage(
                            role=LLMRole.USER,
                            content=trace.content
                        )
                    )

                # Add assistant response (AI_RESPONSE or TUTOR_INTERVENTION)
                elif trace.interaction_type in [
                    InteractionType.AI_RESPONSE.value,
                    InteractionType.TUTOR_INTERVENTION.value
                ] and trace.content:
                    messages.append(
                        LLMMessage(
                            role=LLMRole.ASSISTANT,
                            content=trace.content
                        )
                    )

            # Limit to last N messages to prevent LLM token explosion
            if len(messages) > max_messages:
                original_count = len(messages)
                messages = messages[-max_messages:]
                logger.info(
                    "Truncated conversation history to last %d messages",
                    max_messages,
                    extra={"session_id": session_id, "original_count": original_count}
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

    def get_student_history(
        self,
        student_id: str,
        activity_id: Optional[str] = None
    ) -> List[CognitiveTrace]:
        """
        Get student's trace history from database (STATELESS).

        Args:
            student_id: Student ID
            activity_id: Optional activity ID to filter by

        Returns:
            List of CognitiveTrace objects
        """
        if self.trace_repo is None:
            return []

        # Read from database
        db_traces = self.trace_repo.get_by_student(student_id, limit=100)

        # Convert from ORM to Pydantic
        traces = []
        for db_trace in db_traces:
            try:
                trace = CognitiveTrace(
                    id=db_trace.id,
                    session_id=db_trace.session_id,
                    student_id=db_trace.student_id,
                    activity_id=db_trace.activity_id,
                    trace_level=TraceLevel(db_trace.trace_level),
                    interaction_type=InteractionType(db_trace.interaction_type),
                    content=db_trace.content or "",
                    context=db_trace.context or {},
                    metadata=db_trace.trace_metadata or {},
                    cognitive_state=db_trace.cognitive_state,
                    ai_involvement=db_trace.ai_involvement or 0.5,
                )
                traces.append(trace)
            except Exception as e:
                # Skip invalid traces but log the error
                logger.warning(
                    "Failed to convert database trace to Pydantic model: %s: %s",
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                    extra={
                        "trace_id": db_trace.id if hasattr(db_trace, 'id') else 'unknown',
                        "session_id": db_trace.session_id if hasattr(db_trace, 'session_id') else 'unknown',
                        "student_id": student_id
                    }
                )
                continue

        # Filter by activity_id if specified
        if activity_id:
            traces = [t for t in traces if t.activity_id == activity_id]

        return traces

    def get_trace_sequence(self, session_id: str) -> Optional[TraceSequence]:
        """
        Get trace sequence for a session from database (STATELESS).

        Args:
            session_id: Session ID

        Returns:
            TraceSequence or None if not found
        """
        if self.sequence_repo is None:
            return None

        return self.sequence_repo.get_by_session(session_id)
