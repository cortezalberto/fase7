"""
Base repository utilities and helper functions.

Cortez42: Extracted common utilities from monolithic repositories.py

Provides:
- Enum conversion utilities for safe database operations
- Common imports used across all repositories
"""
from typing import Any, Optional, Type
from enum import Enum
import logging

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _safe_enum_to_str(value: Any, enum_class: Type[Enum]) -> Optional[str]:
    """
    Convert a value to string defensively with enum validation.

    FIXED (2025-11-22): Prevents crashes from invalid enum values in queries
    with enums (TraceLevel, InteractionType, RiskType, RiskLevel, etc.)

    Args:
        value: Can be Enum, str, or None
        enum_class: Enum class for validation

    Returns:
        Lowercase string of the value, or None if value is None

    Raises:
        ValueError: If the value is not valid for the enum
        TypeError: If the type is not supported

    Example:
        >>> from backend.models.trace import TraceLevel
        >>> _safe_enum_to_str(TraceLevel.N4_COGNITIVO, TraceLevel)
        'n4_cognitivo'
        >>> _safe_enum_to_str("N4_COGNITIVO", TraceLevel)
        'n4_cognitivo'
        >>> _safe_enum_to_str("INVALID", TraceLevel)
        ValueError: Invalid TraceLevel: 'INVALID'. Valid values: [...]
    """
    if value is None:
        return None

    # Already a valid enum
    if isinstance(value, enum_class):
        return value.value.lower()

    # Is a string, validate it's a valid enum value
    if isinstance(value, str):
        try:
            # Try to match enum value (case-insensitive)
            value_upper = value.upper()
            for enum_member in enum_class:
                if enum_member.value.upper() == value_upper:
                    return enum_member.value.lower()

            # Not found, raise error with valid values
            valid_values = [e.value for e in enum_class]
            raise ValueError(
                f"Invalid {enum_class.__name__}: '{value}'. "
                f"Valid values: {valid_values}"
            )
        except AttributeError:
            # Malformed enum
            logger.error(
                f"Malformed enum class: {enum_class.__name__}",
                extra={"enum_class": enum_class}
            )
            raise TypeError(f"Malformed enum class: {enum_class.__name__}")

    # Invalid type
    logger.error(
        f"Expected {enum_class.__name__} or str, got {type(value)}",
        extra={"value": value, "type": type(value).__name__}
    )
    raise TypeError(
        f"Expected {enum_class.__name__} or str, got {type(value).__name__}"
    )


def _safe_cognitive_state_to_str(cognitive_state: Optional[Any]) -> Optional[str]:
    """
    Convert CognitiveState to string safely, validating the type.

    Args:
        cognitive_state: Cognitive state (can be CognitiveState enum, str, or None)

    Returns:
        String with the enum value, or None

    Raises:
        ValueError: If cognitive_state is not None, str, or valid CognitiveState
    """
    from ...models.trace import CognitiveState

    if cognitive_state is None:
        return None

    # If already a string, validate it's a valid enum value
    if isinstance(cognitive_state, str):
        try:
            CognitiveState(cognitive_state)
            return cognitive_state
        except ValueError:
            logger.warning(
                f"Invalid cognitive_state string: '{cognitive_state}'. "
                f"Expected one of: {[s.value for s in CognitiveState]}"
            )
            raise ValueError(
                f"Invalid cognitive_state: '{cognitive_state}'. "
                f"Must be one of: {[s.value for s in CognitiveState]}"
            )

    # If it's a CognitiveState enum, extract its value
    if isinstance(cognitive_state, CognitiveState):
        return cognitive_state.value

    # Invalid type
    logger.error(
        f"cognitive_state must be CognitiveState enum or str, got {type(cognitive_state)}"
    )
    raise TypeError(
        f"cognitive_state must be CognitiveState enum or str, got {type(cognitive_state).__name__}"
    )


class BaseRepository:
    """
    Base class for all repositories.

    Provides common database session handling.

    Standard Method Naming Conventions (Cortez66):
    ==============================================

    CRUD Operations:
    - create()             Create new record
    - get_by_id()          Get by internal UUID (primary key)
    - get_by_*()           Get by other fields (e.g., get_by_student())
    - get_all()            Get all records with optional filters
    - update()             Modify record
    - delete()             Remove record (hard delete)
    - soft_delete()        Mark as deleted without removing
    - restore()            Restore soft-deleted record

    Batch Operations:
    - get_by_ids()         Get multiple by internal UUIDs
    - get_by_*_ids()       Get multiple by specific field (e.g., get_by_session_ids())
    - create_batch()       Create multiple records

    Count Operations:
    - count_by_*()         Count records by filter

    State Transitions (domain-specific):
    - end_session()        Session lifecycle
    - publish()            Activity lifecycle
    - archive()            Activity lifecycle
    - resolve_*()          Risk/Alert domain
    - complete_*()         Complete an entity (interview, plan, etc.)

    Association Operations:
    - link_to_*()          Create association
    - unlink_from_*()      Remove association
    - append_*()           Add to collection (e.g., append_question())

    Note: get_by_id() always retrieves by internal UUID.
    For business keys, use specific methods like get_by_activity_id().
    """

    def __init__(self, db_session: Session):
        self.db = db_session
