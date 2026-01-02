"""
Activity Model - Learning activities created by teachers.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- ActivityDB: Database model for learning activities
"""
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, Index, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

from .base import Base, BaseModel


class ActivityDB(Base, BaseModel):
    """Database model for learning activities created by teachers"""

    __tablename__ = "activities"

    # Activity identification
    activity_id = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Activity details
    instructions = Column(Text, nullable=False)  # Consigna detallada
    evaluation_criteria = Column(JSON, default=list)  # Lista de criterios

    # Teacher who created it
    # FIX 2.3: Add FK to users table for teacher_id to ensure referential integrity
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Pedagogical policies (JSON field for flexibility)
    policies = Column(JSON, default=dict, nullable=False)
    # Structure:
    # {
    #   "max_help_level": "MEDIO",  # MINIMO, BAJO, MEDIO, ALTO
    #   "block_complete_solutions": true,
    #   "require_justification": true,
    #   "allow_code_snippets": false,
    #   "risk_thresholds": {
    #     "ai_dependency": 0.6,
    #     "lack_justification": 0.3
    #   }
    # }

    # Metadata
    subject = Column(String(100), nullable=True)  # Ej: "Programacion II"
    difficulty = Column(String(20), nullable=True)  # INICIAL, INTERMEDIO, AVANZADO
    estimated_duration_minutes = Column(Integer, nullable=True)

    # Tags for categorization
    tags = Column(JSON, default=list)  # ["colas", "estructuras", "arreglos"]

    # Activity status
    status = Column(String(20), default="draft")  # draft, active, archived
    published_at = Column(DateTime, nullable=True)

    # FIX 2.3 & 3.4: Add relationship to teacher/user with back_populates
    teacher = relationship("UserDB", back_populates="activities", foreign_keys=[teacher_id])

    # Composite indexes for common query patterns
    __table_args__ = (
        # Query: Get activities by teacher
        Index('idx_activity_teacher_status', 'teacher_id', 'status'),
        # Query: Get active activities
        Index('idx_activity_status_created', 'status', 'created_at'),
        # Query: Search by subject
        Index('idx_activity_subject_status', 'subject', 'status'),
        # FIX 2.5 Cortez6: Check constraint for valid status values
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name='ck_activity_status_valid'
        ),
        # FIX 2.6 Cortez6: Check constraint for valid difficulty values
        CheckConstraint(
            "difficulty IS NULL OR difficulty IN ('INICIAL', 'INTERMEDIO', 'AVANZADO')",
            name='ck_activity_difficulty_valid'
        ),
    )
