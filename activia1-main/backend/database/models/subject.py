"""
Subject Model - Subjects/materias for exercise organization.

Cortez42: Extracted from monolithic models.py (1,772 lines)
FIX Cortez74 (CRIT-INHERIT-001): Now properly inherits from BaseModel

Provides:
- SubjectDB: Database model for subjects (Python, Java, etc.)
"""
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, utc_now


class SubjectDB(Base, BaseModel):
    """
    Database model for subjects/materias (Python, Java, etc.)

    Agrupa ejercicios por lenguaje de programacion y materia.
    Migracion desde JSON a PostgreSQL para centralizar datos.

    FIX Cortez74 (CRIT-INHERIT-001): Now inherits from BaseModel.
    Uses 'code' as additional unique identifier, but keeps standard 'id' UUID
    from BaseModel for consistency across all models.
    """

    __tablename__ = "subjects"

    # Subject identification (using 'code' as unique business key)
    code = Column(String(50), unique=True, nullable=False, index=True)  # 'PYTHON', 'JAVA', 'PROG1'
    name = Column(String(100), nullable=False)  # 'Python', 'Java', 'Programacion 1'
    description = Column(Text, nullable=True)
    language = Column(String(20), nullable=False)  # 'python', 'java'

    # Metadata
    total_units = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    # Note: created_at and updated_at are now inherited from BaseModel

    # Relationships
    exercises = relationship("ExerciseDB", back_populates="subject", cascade="all, delete-orphan")
    unidades = relationship("UnidadDB", back_populates="materia", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_subjects_language', 'language'),
        Index('idx_subjects_active', 'is_active'),
        CheckConstraint("language IN ('python', 'java')", name='check_subject_language'),
    )
