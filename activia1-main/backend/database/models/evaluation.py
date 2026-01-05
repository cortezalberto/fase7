"""
Evaluation Model - Process evaluation database model.

Cortez42: Extracted from monolithic models.py (1,772 lines)
FIX Cortez83: Added GIN indices for JSON columns (PostgreSQL only)

Provides:
- EvaluationDB: Database model for process-based evaluations
"""
from sqlalchemy import (
    Column, String, Float, ForeignKey, JSON, Index, CheckConstraint, event, text
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel


class EvaluationDB(Base, BaseModel):
    """
    Database model for process evaluations.

    Evaluates HOW students solve problems (cognitive process),
    not just the final code output.
    """

    __tablename__ = "evaluations"

    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(String(100), nullable=False, index=True)
    # FIX Cortez68 (MEDIUM): Add index for activity_id lookups
    activity_id = Column(String(100), nullable=False, index=True)

    # Overall assessment
    overall_competency_level = Column(String(50), nullable=False)  # CompetencyLevel
    overall_score = Column(Float, nullable=False)  # 0.0 to 10.0

    # Dimensions (stored as JSON for flexibility)
    dimensions = Column(JSON, default=list)  # List of DimensionEvaluation dicts

    # Feedback
    key_strengths = Column(JSON, default=list)
    improvement_areas = Column(JSON, default=list)
    recommendations = Column(JSON, default=list)

    # Analysis metadata
    reasoning_analysis = Column(JSON, nullable=True)
    git_analysis = Column(JSON, nullable=True)
    ai_dependency_score = Column(Float, default=0.0)  # 0-1 scale
    ai_dependency_metrics = Column(JSON, nullable=True)

    # Relationship
    session = relationship("SessionDB", back_populates="evaluations")

    # Composite indexes
    __table_args__ = (
        Index('idx_eval_student_activity', 'student_id', 'activity_id'),
        Index('idx_competency_score', 'overall_competency_level', 'overall_score'),
        Index('idx_eval_student_created', 'student_id', 'created_at'),
        Index('idx_eval_session_created', 'session_id', 'created_at'),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 10",
            name='ck_eval_score_range'
        ),
        CheckConstraint(
            "ai_dependency_score >= 0 AND ai_dependency_score <= 1",
            name='ck_eval_ai_dep_range'
        ),
    )


# FIX Cortez83: Add GIN indices for JSON columns (PostgreSQL only)
# These are added via DDL event to avoid errors on SQLite
@event.listens_for(EvaluationDB.__table__, "after_create")
def create_gin_indices(target, connection, **kw):
    """Create GIN indices for JSON columns on PostgreSQL."""
    if connection.dialect.name == "postgresql":
        # GIN indices for fast JSON containment queries
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_eval_dimensions_gin
            ON evaluations USING GIN (dimensions jsonb_path_ops);
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_eval_key_strengths_gin
            ON evaluations USING GIN (key_strengths jsonb_path_ops);
        """))
        connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_eval_recommendations_gin
            ON evaluations USING GIN (recommendations jsonb_path_ops);
        """))
