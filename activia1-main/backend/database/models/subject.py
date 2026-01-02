"""
Subject Model - Subjects/materias for exercise organization.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- SubjectDB: Database model for subjects (Python, Java, etc.)
"""
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, utc_now


class SubjectDB(Base):
    """
    Database model for subjects/materias (Python, Java, etc.)

    Agrupa ejercicios por lenguaje de programacion y materia.
    Migracion desde JSON a PostgreSQL para centralizar datos.

    NOTE: No inherits from BaseModel because we use 'code' as PK instead of UUID 'id'
    """

    __tablename__ = "subjects"

    # Subject identification (using 'code' as PK)
    code = Column(String(50), primary_key=True)  # 'PYTHON', 'JAVA', 'PROG1'
    name = Column(String(100), nullable=False)  # 'Python', 'Java', 'Programacion 1'
    description = Column(Text, nullable=True)
    language = Column(String(20), nullable=False)  # 'python', 'java'

    # Metadata
    total_units = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps (manual since not using BaseModel)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    exercises = relationship("ExerciseDB", back_populates="subject", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_subjects_language', 'language'),
        Index('idx_subjects_active', 'is_active'),
        CheckConstraint("language IN ('python', 'java')", name='check_subject_language'),
    )
