"""
Cognitive Trace Model - N4-level cognitive trace database model.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- CognitiveTraceDB: Database model for N4 cognitive traces with 6 dimensions
- TraceSequenceDB: Database model for trace sequences
"""
from sqlalchemy import (
    Column, String, Text, Float, Integer, ForeignKey, Index, CheckConstraint
)
# FIX Cortez91: Removed JSON import - using JSONBCompatible for all JSON columns
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, JSONBCompatible


class CognitiveTraceDB(Base, BaseModel):
    """
    Database model for cognitive traces (N4).

    Implements the 6 dimensions of N4 Traceability:
    1. Semantic: What did the student understand?
    2. Algorithmic: Code evolution and alternatives
    3. Cognitive: Explicit reasoning and justifications
    4. Interactional: Prompts used and AI intervention type
    5. Ethical/Risk: Bias detection and fraud attempts
    6. Processual: Timing and logical sequence
    """

    __tablename__ = "cognitive_traces"

    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False)

    # Trace metadata
    trace_level = Column(String(20), default="n4_cognitivo")  # TraceLevel
    interaction_type = Column(String(50), nullable=False)  # InteractionType

    # Content
    content = Column(Text, nullable=False)
    # FIX Cortez91 CRIT-M01/M02: Changed JSON to JSONBCompatible for SQLite test compatibility
    context = Column(JSONBCompatible, default=dict)
    trace_metadata = Column(JSONBCompatible, default=dict)

    # N4 Cognitive analysis
    cognitive_state = Column(String(50), nullable=True)
    cognitive_intent = Column(String(200), nullable=True)
    decision_justification = Column(Text, nullable=True)
    alternatives_considered = Column(JSONBCompatible, default=list)
    strategy_type = Column(String(100), nullable=True)

    # AI involvement (0.0 to 1.0)
    ai_involvement = Column(Float, default=0.0)

    # === 6 DIMENSIONS OF N4 TRACEABILITY ===

    # 1. SEMANTIC DIMENSION
    semantic_understanding = Column(JSONBCompatible, default=dict, nullable=True)

    # 2. ALGORITHMIC DIMENSION
    algorithmic_evolution = Column(JSONBCompatible, default=dict, nullable=True)

    # 3. COGNITIVE DIMENSION
    cognitive_reasoning = Column(JSONBCompatible, default=dict, nullable=True)

    # 4. INTERACTIONAL DIMENSION
    interactional_data = Column(JSONBCompatible, default=dict, nullable=True)

    # 5. ETHICAL/RISK DIMENSION
    ethical_risk_data = Column(JSONBCompatible, default=dict, nullable=True)

    # 6. PROCESSUAL DIMENSION
    process_data = Column(JSONBCompatible, default=dict, nullable=True)

    # Relationships
    session = relationship("SessionDB", back_populates="traces")

    # Self-referential hierarchy
    parent_trace_id = Column(
        String(36),
        ForeignKey("cognitive_traces.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    parent_trace = relationship(
        "CognitiveTraceDB",
        remote_side="CognitiveTraceDB.id",
        backref="child_traces",
        foreign_keys=[parent_trace_id]
    )
    agent_id = Column(String(100), nullable=True)

    # Composite indexes
    __table_args__ = (
        Index('idx_trace_session_interaction', 'session_id', 'interaction_type'),
        Index('idx_trace_student_created', 'student_id', 'created_at'),
        Index('idx_student_activity_state', 'student_id', 'activity_id', 'cognitive_state'),
        Index('idx_session_level', 'session_id', 'trace_level'),
        Index('idx_session_created_desc', 'session_id', 'created_at'),
        Index('idx_trace_activity', 'activity_id'),
        CheckConstraint(
            "trace_level IN ('n1_superficial', 'n2_tecnico', 'n3_interaccional', 'n4_cognitivo')",
            name='ck_trace_level_valid'
        ),
        # FIX Cortez74 (MED-DB-002): Add CheckConstraint for interaction_type enum values
        CheckConstraint(
            "interaction_type IN ("
            "'student_prompt', 'ai_response', 'code_commit', 'tutor_intervention', "
            "'teacher_feedback', 'strategy_change', 'hypothesis_formulation', "
            "'self_correction', 'ai_critique'"
            ")",
            name='ck_trace_interaction_type_valid'
        ),
        # GIN indexes for JSONB columns (PostgreSQL only)
        Index('idx_trace_semantic_gin', 'semantic_understanding', postgresql_using='gin'),
        Index('idx_trace_algorithmic_gin', 'algorithmic_evolution', postgresql_using='gin'),
        Index('idx_trace_cognitive_gin', 'cognitive_reasoning', postgresql_using='gin'),
        Index('idx_trace_interactional_gin', 'interactional_data', postgresql_using='gin'),
        Index('idx_trace_ethical_gin', 'ethical_risk_data', postgresql_using='gin'),
        Index('idx_trace_process_gin', 'process_data', postgresql_using='gin'),
        CheckConstraint(
            "ai_involvement >= 0 AND ai_involvement <= 1",
            name='ck_trace_ai_involvement_range'
        ),
    )


class TraceSequenceDB(Base, BaseModel):
    """
    Database model for trace sequences.

    Aggregates session-level N4 metrics for comprehensive traceability.
    """

    __tablename__ = "trace_sequences"

    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=False)

    # Aggregated metrics
    # FIX Cortez69 CRIT-DB-001: Changed from Float to Integer (trace count is always integer)
    total_traces = Column(Integer, default=0)
    avg_ai_involvement = Column(Float, default=0.0)
    # FIX Cortez91: Changed JSON to JSONBCompatible for SQLite test compatibility
    detected_risks = Column(JSONBCompatible, default=list)
    competencies = Column(JSONBCompatible, default=dict)

    # N4 Summary dimensions
    semantic_summary = Column(JSONBCompatible, default=dict, nullable=True)
    algorithmic_summary = Column(JSONBCompatible, default=dict, nullable=True)
    cognitive_summary = Column(JSONBCompatible, default=dict, nullable=True)
    interaction_summary = Column(JSONBCompatible, default=dict, nullable=True)
    ethics_summary = Column(JSONBCompatible, default=dict, nullable=True)
    process_summary = Column(JSONBCompatible, default=dict, nullable=True)

    # Session relationship
    session = relationship("SessionDB", back_populates="trace_sequences")

    __table_args__ = (
        Index('idx_sequence_session', 'session_id'),
        Index('idx_sequence_student', 'student_id'),
        Index('idx_sequence_activity', 'activity_id'),
        Index('idx_sequence_student_activity', 'student_id', 'activity_id'),
    )
