"""
Base repository utilities and helper functions.

Cortez42: Extracted common utilities from monolithic repositories.py
Cortez89: Enhanced BaseRepository with Generic CRUD methods (P1 refactoring)

Provides:
- Enum conversion utilities for safe database operations
- Common imports used across all repositories
- Generic BaseRepository with reusable CRUD operations
- GenericRepository[T] for type-safe repository implementations
"""
from typing import Any, Optional, Type, TypeVar, Generic, List, Dict, Callable
from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Type variable for generic repository
T = TypeVar("T")


def _safe_enum_to_str(value: Any, enum_class: Type[Enum]) -> Optional[str]:
    """
    Convert a value to string defensively with enum validation.

    FIXED (2025-11-22): Prevents crashes from invalid enum values in queries
    with enums (TraceLevel, InteractionType, RiskType, RiskLevel, etc.)

    FIXED (Cortez92 HIGH-003): Handle non-string enum values safely

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
        # HIGH-003 FIX: Handle non-string enum values safely
        enum_value = value.value
        if enum_value is None:
            return None
        return str(enum_value).lower()

    # Is a string, validate it's a valid enum value
    if isinstance(value, str):
        try:
            # Try to match enum value (case-insensitive)
            value_upper = value.upper()
            for enum_member in enum_class:
                # HIGH-003 FIX: Safe handling of enum member values
                member_value = enum_member.value
                if member_value is None:
                    continue
                member_str = str(member_value)
                if member_str.upper() == value_upper:
                    return member_str.lower()

            # Not found, raise error with valid values
            valid_values = [str(e.value) for e in enum_class if e.value is not None]
            raise ValueError(
                f"Invalid {enum_class.__name__}: '{value}'. "
                f"Valid values: {valid_values}"
            )
        except AttributeError:
            # Malformed enum - use lazy logging (CRIT-002 FIX)
            logger.error(
                "Malformed enum class: %s",
                enum_class.__name__,
                extra={"enum_class": str(enum_class)}
            )
            raise TypeError(f"Malformed enum class: {enum_class.__name__}")

    # Invalid type - use lazy logging (CRIT-002 FIX)
    logger.error(
        "Expected %s or str, got %s",
        enum_class.__name__,
        type(value).__name__,
        extra={"value": str(value), "type": type(value).__name__}
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


class GenericRepository(Generic[T]):
    """
    Cortez89: Generic Repository with reusable CRUD operations.

    Provides type-safe, DRY implementations of common database operations.
    Subclasses should set the `model` class attribute to the ORM model class.

    Example usage:
        class MyRepository(GenericRepository[MyModelDB]):
            model = MyModelDB

            # Add domain-specific methods here
            def get_by_custom_field(self, value: str) -> Optional[MyModelDB]:
                return self.db.query(self.model).filter(
                    self.model.custom_field == value
                ).first()

    Benefits:
    - Eliminates ~500 lines of duplicated CRUD code across repositories
    - Type-safe with Generic[T] for IDE autocompletion
    - Consistent error handling with try/except/rollback
    - Supports soft delete pattern (deleted_at column)
    - Pessimistic locking via with_for_update() option
    """

    # Subclasses MUST set this to their ORM model class
    model: Type[T]

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db = db_session

    # =========================================================================
    # CREATE Operations
    # =========================================================================

    def create(self, **kwargs) -> T:
        """
        Create a new record.

        Args:
            **kwargs: Field values for the new record

        Returns:
            Created model instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            # Auto-generate UUID id if not provided and model has id field
            if "id" not in kwargs and hasattr(self.model, "id"):
                kwargs["id"] = str(uuid4())

            entity = self.model(**kwargs)
            self.db.add(entity)
            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to create %s: %s",
                self.model.__name__,
                str(e),
                exc_info=True
            )
            raise

    def create_batch(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in a single transaction.

        Args:
            items: List of dictionaries with field values

        Returns:
            List of created model instances

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entities = []
            for item in items:
                if "id" not in item and hasattr(self.model, "id"):
                    item["id"] = str(uuid4())
                entity = self.model(**item)
                entities.append(entity)

            self.db.add_all(entities)
            self.db.commit()

            for entity in entities:
                self.db.refresh(entity)

            logger.debug("Batch created %d %s records", len(entities), self.model.__name__)
            return entities
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to batch create %s: %s",
                self.model.__name__,
                str(e),
                exc_info=True
            )
            raise

    # =========================================================================
    # READ Operations
    # =========================================================================

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """
        Get record by internal UUID (primary key).

        Args:
            entity_id: UUID string of the record

        Returns:
            Model instance if found, None otherwise
        """
        return self.db.query(self.model).filter(self.model.id == entity_id).first()

    def get_by_ids(
        self,
        entity_ids: List[str],
        warn_on_missing: bool = True
    ) -> Dict[str, T]:
        """
        Get multiple records by IDs in a single query (batch loading).

        Prevents N+1 queries when loading multiple records.

        HIGH-002 FIX (Cortez92): Added logging for missing IDs to help debug
        cases where some requested records don't exist.

        Args:
            entity_ids: List of UUID strings
            warn_on_missing: If True, logs warning when some IDs are not found

        Returns:
            Dictionary mapping entity_id to model instance.
            Note: Missing IDs will not be in the returned dict.
        """
        if not entity_ids:
            return {}

        entities = (
            self.db.query(self.model)
            .filter(self.model.id.in_(entity_ids))
            .all()
        )
        result = {str(entity.id): entity for entity in entities}

        # HIGH-002 FIX: Log warning if some IDs were not found
        if warn_on_missing and len(result) < len(entity_ids):
            missing_ids = set(entity_ids) - set(result.keys())
            if missing_ids:
                logger.warning(
                    "%s.get_by_ids: %d of %d IDs not found: %s",
                    self.model.__name__,
                    len(missing_ids),
                    len(entity_ids),
                    list(missing_ids)[:5]  # Limit to first 5 for log brevity
                )

        return result

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by_desc: Optional[str] = "created_at",
        filters: Optional[Dict[str, Any]] = None,
        exclude_deleted: bool = True
    ) -> List[T]:
        """
        Get all records with optional filters, pagination, and ordering.

        Args:
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)
            order_by_desc: Field name for descending order (default: created_at)
            filters: Dictionary of field_name: value for filtering
            exclude_deleted: If True and model has deleted_at, excludes soft-deleted

        Returns:
            List of model instances
        """
        query = self.db.query(self.model)

        # Apply soft delete filter if applicable
        if exclude_deleted and hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))

        # Apply custom filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        # Apply ordering
        if order_by_desc and hasattr(self.model, order_by_desc):
            query = query.order_by(desc(getattr(self.model, order_by_desc)))

        return query.limit(limit).offset(offset).all()

    def exists(self, entity_id: str) -> bool:
        """
        Check if record exists without loading full object.

        Args:
            entity_id: UUID string of the record

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(
            self.db.query(self.model).filter(self.model.id == entity_id).exists()
        ).scalar()

    def count(self, filters: Optional[Dict[str, Any]] = None, exclude_deleted: bool = True) -> int:
        """
        Count records with optional filters.

        Args:
            filters: Dictionary of field_name: value for filtering
            exclude_deleted: If True and model has deleted_at, excludes soft-deleted

        Returns:
            Number of matching records
        """
        query = self.db.query(func.count(self.model.id))

        if exclude_deleted and hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)

        return query.scalar() or 0

    # =========================================================================
    # UPDATE Operations
    # =========================================================================

    def update(
        self,
        entity_id: str,
        use_locking: bool = True,
        **kwargs
    ) -> Optional[T]:
        """
        Update record fields with optional pessimistic locking.

        Args:
            entity_id: UUID of record to update
            use_locking: If True, uses SELECT FOR UPDATE (default: True)
            **kwargs: Fields to update

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            if use_locking:
                stmt = select(self.model).where(self.model.id == entity_id).with_for_update()
                entity = self.db.execute(stmt).scalar_one_or_none()
            else:
                entity = self.get_by_id(entity_id)

            if not entity:
                return None

            for key, value in kwargs.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            # Update timestamp if model has updated_at
            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to update %s %s: %s",
                self.model.__name__,
                entity_id,
                str(e),
                exc_info=True
            )
            raise

    # =========================================================================
    # DELETE Operations
    # =========================================================================

    def delete(self, entity_id: str) -> bool:
        """
        Hard delete a record.

        WARNING: This permanently removes the record and may cascade.

        Args:
            entity_id: UUID of record to delete

        Returns:
            True if deleted, False if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            entity = self.get_by_id(entity_id)
            if not entity:
                return False

            self.db.delete(entity)
            self.db.commit()
            logger.debug("Deleted %s: %s", self.model.__name__, entity_id)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to delete %s %s: %s",
                self.model.__name__,
                entity_id,
                str(e),
                exc_info=True
            )
            raise

    def soft_delete(self, entity_id: str) -> Optional[T]:
        """
        Soft delete a record by setting deleted_at timestamp.

        Requires model to have a `deleted_at` column.

        Args:
            entity_id: UUID of record to soft delete

        Returns:
            Updated model instance if found, None otherwise

        Raises:
            AttributeError: If model doesn't have deleted_at column
            SQLAlchemyError: If database operation fails
        """
        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"{self.model.__name__} doesn't support soft delete (no deleted_at column)"
            )

        try:
            stmt = select(self.model).where(self.model.id == entity_id).with_for_update()
            entity = self.db.execute(stmt).scalar_one_or_none()

            if not entity:
                return None

            entity.deleted_at = datetime.now(timezone.utc)

            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(entity)
            logger.debug("Soft deleted %s: %s", self.model.__name__, entity_id)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to soft delete %s %s: %s",
                self.model.__name__,
                entity_id,
                str(e),
                exc_info=True
            )
            raise

    def restore(self, entity_id: str) -> Optional[T]:
        """
        Restore a soft-deleted record by clearing deleted_at.

        Args:
            entity_id: UUID of record to restore

        Returns:
            Restored model instance if found, None otherwise

        Raises:
            AttributeError: If model doesn't have deleted_at column
            SQLAlchemyError: If database operation fails
        """
        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"{self.model.__name__} doesn't support restore (no deleted_at column)"
            )

        try:
            # Include soft-deleted records in query
            stmt = select(self.model).where(self.model.id == entity_id).with_for_update()
            entity = self.db.execute(stmt).scalar_one_or_none()

            if not entity:
                return None

            entity.deleted_at = None

            if hasattr(entity, "updated_at"):
                entity.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(entity)
            logger.debug("Restored %s: %s", self.model.__name__, entity_id)
            return entity
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(
                "Failed to restore %s %s: %s",
                self.model.__name__,
                entity_id,
                str(e),
                exc_info=True
            )
            raise

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_or_create(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        validate_fields: bool = True,
        **lookup_kwargs
    ) -> tuple[T, bool]:
        """
        Get existing record or create new one.

        HIGH-005 FIX (Cortez92): Added field validation to prevent silent failures
        when invalid field names are passed.

        Args:
            defaults: Default values for creation (not used for lookup)
            validate_fields: If True, raises ValueError for invalid field names
            **lookup_kwargs: Fields to match for lookup

        Returns:
            Tuple of (instance, created) where created is True if new record

        Raises:
            ValueError: If validate_fields=True and an invalid field name is passed
            SQLAlchemyError: If database operation fails
        """
        query = self.db.query(self.model)

        for field, value in lookup_kwargs.items():
            if hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
            elif validate_fields:
                # HIGH-005 FIX: Raise error for invalid fields instead of silently ignoring
                valid_fields = [c.name for c in self.model.__table__.columns]
                raise ValueError(
                    f"Invalid field '{field}' for {self.model.__name__}. "
                    f"Valid fields: {valid_fields}"
                )
            else:
                # Legacy behavior: log warning but continue
                logger.warning(
                    "get_or_create: Invalid field '%s' for %s, ignoring",
                    field,
                    self.model.__name__
                )

        entity = query.first()
        if entity:
            return entity, False

        # Create new record
        create_kwargs = {**lookup_kwargs, **(defaults or {})}
        entity = self.create(**create_kwargs)
        return entity, True
