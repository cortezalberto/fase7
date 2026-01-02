"""
Session Model - Learning session database model.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- SessionDB: Database model for learning sessions with N4 traceability metadata
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, JSONBCompatible, utc_now


class SessionDB(Base, BaseModel):
    """
    Database model for learning sessions.

    Includes Learning Objective and Cognitive Status metadata for N4 traceability.

    IMPORTANT: user_id is nullable to support:
    1. Anonymous sessions (guest users without authentication)
    2. Legacy data (sessions created before user authentication)
    3. Programmatic sessions (created by scripts, tests, or automated processes)
    """

    __tablename__ = "sessions"

    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False, index=True)
    mode = Column(String(50), nullable=False, default="tutor")  # AgentMode

    # Simulator type (when mode=SIMULATOR)
    simulator_type = Column(String(50), nullable=True, index=True)

    # User authentication relationship (nullable for backwards compatibility)
    user_id = Column(
        String(36),
        ForeignKey('users.id', ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Session metadata
    start_time = Column(DateTime, default=utc_now, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active, completed, abandoned

    # === N4 TRACEABILITY METADATA ===

    # Learning objective for this session
    learning_objective = Column(JSONBCompatible, default=dict, nullable=True)
    # {
    #   "title": "Implement Queue data structure",
    #   "description": "Understand and apply FIFO concept",
    #   "expected_competencies": ["abstraction", "implementation", "testing"],
    #   "difficulty_level": "intermediate"
    # }

    # Cognitive status (updated dynamically)
    cognitive_status = Column(JSONBCompatible, default=dict, nullable=True)
    # {
    #   "current_phase": "exploration|planning|implementation|debugging|validation|reflection",
    #   "autonomy_level": 0.0-1.0,
    #   "engagement_score": 0.0-1.0,
    #   "cognitive_load": "low|medium|high|overload",
    #   "last_updated": "timestamp"
    # }

    # Aggregated session metrics (calculated on completion)
    session_metrics = Column(JSONBCompatible, default=dict, nullable=True)
    # {
    #   "total_interactions": 15,
    #   "ai_dependency_score": 0.65,
    #   "risk_events": 3,
    #   "autonomy_progression": [0.3, 0.5, 0.7],
    #   "competencies_demonstrated": ["abstraction", "debugging"]
    # }

    # Relationships
    user = relationship("UserDB", back_populates="sessions")
    traces = relationship(
        "CognitiveTraceDB", back_populates="session", cascade="all, delete-orphan"
    )
    risks = relationship(
        "RiskDB", back_populates="session", cascade="all, delete-orphan"
    )
    evaluations = relationship(
        "EvaluationDB", back_populates="session", cascade="all, delete-orphan"
    )
    simulator_events = relationship(
        "SimulatorEventDB", back_populates="session", cascade="all, delete-orphan"
    )
    git_traces = relationship(
        "GitTraceDB", back_populates="session", cascade="all, delete-orphan"
    )
    interview_sessions = relationship(
        "InterviewSessionDB", back_populates="session", cascade="all, delete-orphan"
    )
    incident_simulations = relationship(
        "IncidentSimulationDB", back_populates="session", cascade="all, delete-orphan"
    )
    lti_sessions = relationship(
        "LTISessionDB", back_populates="session", cascade="all, delete-orphan"
    )
    trace_sequences = relationship(
        "TraceSequenceDB", back_populates="session", cascade="all, delete-orphan"
    )

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_session_student_activity', 'student_id', 'activity_id'),
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_student_status', 'student_id', 'status'),
        Index('idx_session_status', 'status'),
        Index('idx_session_mode_status', 'mode', 'status'),
        CheckConstraint(
            "status IN ('active', 'completed', 'paused', 'aborted', 'abandoned')",
            name='ck_session_status_valid'
        ),
        CheckConstraint(
            "mode IN ('tutor', 'simulator', 'evaluator', 'risk_analyst', 'governance', 'practice', 'TUTOR', 'SIMULATOR', 'EVALUATOR', 'RISK_ANALYST', 'GOVERNANCE', 'PRACTICE')",
            name='ck_session_mode_valid'
        ),
        CheckConstraint(
            "simulator_type IS NULL OR simulator_type IN ('product_owner', 'scrum_master', 'tech_interviewer', 'incident_responder', 'client', 'devsecops', 'senior_dev', 'qa_engineer', 'security_auditor', 'tech_lead', 'demanding_client')",
            name='ck_session_simulator_type_valid'
        ),
    )
