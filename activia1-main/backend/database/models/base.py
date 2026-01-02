"""
Base Model Utilities - Common components for all ORM models.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- JSONBCompatible: Cross-database JSON type (PostgreSQL JSONB / SQLite JSON)
- _utc_now: Timezone-aware UTC timestamp helper
- Re-exports from database.base for convenience
"""
from datetime import datetime, timezone

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

# Re-export from database.base
from ..base import Base, BaseModel


class JSONBCompatible(TypeDecorator):
    """
    A JSON type that uses JSONB on PostgreSQL and JSON on other databases.

    This allows tests to run with SQLite while production uses PostgreSQL
    with JSONB for better indexing and query performance.

    Usage:
        metadata = Column(JSONBCompatible, default=dict)
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


def utc_now():
    """
    Helper for SQLAlchemy default - returns timezone-aware UTC timestamp.

    Usage:
        created_at = Column(DateTime, default=utc_now, nullable=False)
    """
    return datetime.now(timezone.utc)


__all__ = [
    "Base",
    "BaseModel",
    "JSONBCompatible",
    "utc_now",
]
