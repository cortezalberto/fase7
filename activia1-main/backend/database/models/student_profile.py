"""
Student Profile Model - Student learning profiles.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- StudentProfileDB: Database model for student learning profiles
"""
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, CheckConstraint, JSON, ForeignKey
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, JSONBCompatible


class StudentProfileDB(Base, BaseModel):
    """Database model for student learning profiles"""

    __tablename__ = "student_profiles"

    # FIX 2.2: Keep student_id as logical key, add user_id FK for authenticated users
    student_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Profile metadata
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True)

    # Learning analytics
    total_sessions = Column(Integer, default=0)
    total_interactions = Column(Integer, default=0)
    average_ai_dependency = Column(Float, default=0.0)
    average_competency_level = Column(String(50), nullable=True)
    # FIX 10.2 Cortez10: Added average_competency_score to match schema expectations
    average_competency_score = Column(Float, nullable=True)  # Score 0-10

    # Risk profile
    total_risks = Column(Integer, default=0)
    critical_risks = Column(Integer, default=0)
    risk_trends = Column(JSON, default=dict)

    # Progress tracking
    competency_evolution = Column(JSON, default=list)  # Time series data
    last_activity_date = Column(DateTime, nullable=True)

    # FIX 10.2 Cortez10: Added missing fields to match schema expectations
    preferred_language = Column(String(10), default="es", nullable=True)
    cognitive_preferences = Column(JSONBCompatible, default=dict, nullable=True)
    learning_patterns = Column(JSONBCompatible, default=dict, nullable=True)
    competency_levels = Column(JSONBCompatible, default=dict, nullable=True)  # {"area": "level"}
    strengths = Column(JSON, default=list, nullable=True)
    areas_for_improvement = Column(JSON, default=list, nullable=True)

    # FIX 2.2 & 3.4: Add relationship to UserDB with back_populates
    user = relationship("UserDB", back_populates="student_profiles", foreign_keys=[user_id])

    # FIX 2.15 Cortez6: Range constraint for average_ai_dependency
    # FIX 10.2 Cortez10: Added constraint for average_competency_score
    __table_args__ = (
        CheckConstraint(
            "average_ai_dependency >= 0 AND average_ai_dependency <= 1",
            name='ck_profile_ai_dep_range'
        ),
        CheckConstraint(
            "average_competency_score IS NULL OR (average_competency_score >= 0 AND average_competency_score <= 10)",
            name='ck_profile_competency_score_range'
        ),
    )
