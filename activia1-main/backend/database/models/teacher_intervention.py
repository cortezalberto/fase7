"""
Teacher Intervention Model - Teacher intervention tracking.

Cortez82: Created for persistencia de reconocimiento de alertas (Mejora 4.1)

Provides:
- TeacherInterventionDB: Database model for teacher interventions on student alerts
"""
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from .base import Base, BaseModel, utc_now, JSONBCompatible


class TeacherInterventionDB(Base, BaseModel):
    """
    Database model for teacher interventions.

    Tracks when teachers acknowledge alerts, intervene with students,
    and the outcomes of those interventions.

    This solves the problem where alert acknowledgments were not persisted
    and lost on server restart.
    """

    __tablename__ = "teacher_interventions"

    # Foreign keys
    teacher_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(String(100), nullable=False, index=True)
    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    alert_id = Column(String(100), nullable=True, index=True)

    # Intervention details
    intervention_type = Column(
        String(50),
        nullable=False,
        default="alert_acknowledgment"
    )
    # Types: alert_acknowledgment, direct_message, grade_adjustment,
    #        remediation_plan, meeting_scheduled, resource_shared

    # Content
    notes = Column(Text, nullable=True)
    action_taken = Column(Text, nullable=True)

    # Status tracking
    status = Column(String(30), default="acknowledged")
    # Status: acknowledged, in_progress, resolved, escalated, closed

    # Resolution
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Context (stores original alert data for historical reference)
    # FIX Cortez85 HIGH-ORM-003: Use JSONBCompatible instead of type_=None
    alert_context: Mapped[Optional[dict]] = mapped_column(
        JSONBCompatible,
        nullable=True,
        default=None
    )

    # Relationships
    # FIX Cortez83: Added back_populates for bidirectional navigation
    teacher = relationship("UserDB", back_populates="teacher_interventions", foreign_keys=[teacher_id])
    session = relationship("SessionDB", back_populates="teacher_interventions", foreign_keys=[session_id])

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_intervention_teacher_status', 'teacher_id', 'status'),
        Index('idx_intervention_student', 'student_id'),
        Index('idx_intervention_alert', 'alert_id'),
        Index('idx_intervention_created', 'created_at'),
        Index('idx_intervention_type_status', 'intervention_type', 'status'),
        CheckConstraint(
            "intervention_type IN ('alert_acknowledgment', 'direct_message', "
            "'grade_adjustment', 'remediation_plan', 'meeting_scheduled', "
            "'resource_shared', 'follow_up')",
            name='ck_intervention_type_valid'
        ),
        CheckConstraint(
            "status IN ('acknowledged', 'in_progress', 'resolved', 'escalated', 'closed')",
            name='ck_intervention_status_valid'
        ),
    )
