"""
Risk Model - Risk database model.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- RiskDB: Database model for detected risks
"""
from sqlalchemy import (
    Column, String, Text, Float, Boolean, DateTime, ForeignKey, JSON,
    Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel


class RiskDB(Base, BaseModel):
    """
    Database model for detected risks.

    A risk is ALWAYS associated with a session, as without a session
    there is no context (student, activity, time, related traces).
    """

    __tablename__ = "risks"

    # REQUIRED: A risk without session has no valid context
    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(String(100), nullable=False, index=True)
    # FIX Cortez68 (MEDIUM): Add index for activity_id lookups
    activity_id = Column(String(100), nullable=False, index=True)

    # Risk classification
    risk_type = Column(String(100), nullable=False)  # RiskType
    risk_level = Column(String(20), nullable=False)  # RiskLevel
    dimension = Column(String(50), nullable=False)  # RiskDimension

    # Description
    description = Column(Text, nullable=False)
    impact = Column(Text, nullable=True)
    evidence = Column(JSON, default=list)
    trace_ids = Column(JSON, default=list)

    # Analysis
    root_cause = Column(Text, nullable=True)
    impact_assessment = Column(Text, nullable=True)

    # Recommendations
    recommendations = Column(JSON, default=list)
    pedagogical_intervention = Column(Text, nullable=True)

    # Status
    resolved = Column(Boolean, default=False, server_default='false')
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    detected_by = Column(String(50), default="AR-IA")

    # Relationship
    session = relationship("SessionDB", back_populates="risks")

    # Composite indexes
    __table_args__ = (
        Index('idx_student_resolved', 'student_id', 'resolved'),
        Index('idx_level_created', 'risk_level', 'created_at'),
        Index('idx_student_activity_dimension', 'student_id', 'activity_id', 'dimension'),
        Index('idx_risk_session_type', 'session_id', 'risk_type'),
        Index('idx_risk_session_resolved', 'session_id', 'resolved'),
        Index('idx_risk_session_level', 'session_id', 'risk_level'),
        Index('idx_risk_resolved_at', 'resolved_at'),
        CheckConstraint(
            "risk_level IN ('low', 'medium', 'high', 'critical', 'info')",
            name='ck_risk_level_valid'
        ),
    )
