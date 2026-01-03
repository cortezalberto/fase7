"""
Simulation Models - Interview sessions, incident simulations, and simulator events.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- InterviewSessionDB: Technical interview sessions
- IncidentSimulationDB: Incident response simulations
- SimulatorEventDB: Simulator event tracking
"""
from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime,
    ForeignKey, JSON, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, utc_now


class InterviewSessionDB(Base, BaseModel):
    """
    Interview sessions conducted by Technical Interviewer Agent (IT-IA)

    Stores interview questions, responses, and evaluation for HU-EST-011
    """

    __tablename__ = "interview_sessions"

    # FIX 3.2 Cortez3: Added ondelete="CASCADE" to prevent orphan records
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    # FIX Cortez68 (MEDIUM): Add index for activity_id lookups
    activity_id = Column(String(100), nullable=True, index=True)

    # Interview type
    interview_type = Column(String(50), nullable=False)  # "CONCEPTUAL", "ALGORITHMIC", "DESIGN", "BEHAVIORAL"
    # FIX Cortez36: Enum values should be lowercase per CLAUDE.md conventions
    difficulty_level = Column(String(20), default="medium")  # "easy", "medium", "hard"

    # Questions and responses
    questions_asked = Column(JSON, default=list)
    # List of:
    # {
    #   "question": "Explain polymorphism",
    #   "type": "conceptual",
    #   "expected_key_points": ["dynamic binding", "inheritance", "abstraction"],
    #   "timestamp": "2025-11-21T10:30:00Z"
    # }

    responses = Column(JSON, default=list)
    # List of:
    # {
    #   "question_id": 0,
    #   "response": "Student's answer",
    #   "evaluation": {
    #     "clarity_score": 0.8,
    #     "technical_accuracy": 0.7,
    #     "thinking_aloud": true,
    #     "key_points_covered": ["dynamic binding", "inheritance"]
    #   },
    #   "timestamp": "2025-11-21T10:32:00Z"
    # }

    # Overall evaluation
    evaluation_score = Column(Float, nullable=True)  # 0.0 - 1.0
    evaluation_breakdown = Column(JSON, default=dict)
    # {
    #   "clarity": 0.8,
    #   "technical_accuracy": 0.7,
    #   "communication": 0.9,
    #   "problem_solving": 0.75
    # }

    feedback = Column(Text, nullable=True)  # Detailed feedback for student

    # Duration
    duration_minutes = Column(Integer, nullable=True)

    # Relationship
    session = relationship("SessionDB", back_populates="interview_sessions")

    # Composite indexes
    __table_args__ = (
        # Query: Get interviews for a student ordered by date
        Index('idx_interview_student_created', 'student_id', 'created_at'),
        # Query: Get interviews by type and difficulty
        Index('idx_interview_type_difficulty', 'interview_type', 'difficulty_level'),
        # FIX 2.1 Cortez6: Check constraint for valid interview_type values
        CheckConstraint(
            "interview_type IN ('CONCEPTUAL', 'ALGORITHMIC', 'DESIGN', 'BEHAVIORAL')",
            name='ck_interview_type_valid'
        ),
        # FIX 2.2 Cortez6: Check constraint for valid difficulty_level values
        # FIX Cortez68 (MEDIUM): Case-insensitive - accept both lowercase (default) and uppercase
        CheckConstraint(
            "UPPER(difficulty_level) IN ('EASY', 'MEDIUM', 'HARD')",
            name='ck_interview_difficulty_valid'
        ),
        # FIX 2.15 Cortez6: Range constraint for evaluation_score
        CheckConstraint(
            "evaluation_score IS NULL OR (evaluation_score >= 0 AND evaluation_score <= 1)",
            name='ck_interview_score_range'
        ),
    )


class IncidentSimulationDB(Base, BaseModel):
    """
    Incident response simulations conducted by Incident Responder Agent (IR-IA)

    Stores incident scenarios, diagnosis process, and evaluation for HU-EST-012
    """

    __tablename__ = "incident_simulations"

    # FIX 3.2 Cortez3: Added ondelete="CASCADE" to prevent orphan records
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    # FIX Cortez68 (MEDIUM): Add index for activity_id lookups
    activity_id = Column(String(100), nullable=True, index=True)

    # Incident type
    incident_type = Column(String(50), nullable=False)  # "API_ERROR", "PERFORMANCE", "SECURITY", "DATABASE", "DEPLOYMENT"
    # FIX Cortez36: Enum values should be lowercase per CLAUDE.md conventions
    severity = Column(String(20), default="high")  # "low", "medium", "high", "critical"

    # Incident description
    incident_description = Column(Text, nullable=False)
    # e.g., "API is returning 500 in 30% of requests. Users reporting timeouts."

    simulated_logs = Column(Text, nullable=True)  # Simulated error logs
    simulated_metrics = Column(JSON, default=dict)  # Simulated monitoring metrics

    # Diagnosis process (captured as trace)
    diagnosis_process = Column(JSON, default=list)
    # List of:
    # {
    #   "step": 1,
    #   "action": "Checked application logs",
    #   "finding": "Found NullPointerException in UserService",
    #   "timestamp": "2025-11-21T11:00:00Z"
    # }

    # Solution proposed
    solution_proposed = Column(Text, nullable=True)
    root_cause_identified = Column(Text, nullable=True)

    # Timing
    time_to_diagnose_minutes = Column(Integer, nullable=True)
    time_to_resolve_minutes = Column(Integer, nullable=True)

    # Post-mortem documentation
    post_mortem = Column(Text, nullable=True)
    # Structured post-mortem with sections:
    # - What happened
    # - Root cause
    # - Resolution
    # - Prevention measures

    # Evaluation
    evaluation = Column(JSON, default=dict)
    # {
    #   "diagnosis_systematic": 0.8,  # Did they follow a systematic approach?
    #   "prioritization": 0.7,  # Did they prioritize correctly?
    #   "documentation": 0.9,  # Quality of post-mortem
    #   "communication": 0.85  # How well they communicated the incident
    # }

    # Relationship
    session = relationship("SessionDB", back_populates="incident_simulations")

    # Composite indexes
    __table_args__ = (
        # Query: Get incidents for a student ordered by date
        Index('idx_incident_student_created', 'student_id', 'created_at'),
        # Query: Get incidents by type and severity
        Index('idx_incident_type_severity', 'incident_type', 'severity'),
        # FIX 2.3 Cortez6: Check constraint for valid incident_type values
        CheckConstraint(
            "incident_type IN ('API_ERROR', 'PERFORMANCE', 'SECURITY', 'DATABASE', 'DEPLOYMENT')",
            name='ck_incident_type_valid'
        ),
        # FIX 2.4 Cortez6: Check constraint for valid severity values
        # FIX Cortez68 (MEDIUM): Case-insensitive - accept both lowercase (default) and uppercase
        CheckConstraint(
            "UPPER(severity) IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name='ck_incident_severity_valid'
        ),
    )


class SimulatorEventDB(Base, BaseModel):
    """
    Simulator Events - Captura eventos generados por simuladores

    Tipos de eventos:
    - backlog_created: Product Owner creo backlog
    - sprint_planning_complete: Scrum Master completo planning
    - sprint_planning_failed: Fallo en planificacion
    - user_story_approved: Historia de usuario aprobada
    - technical_decision_made: Decision tecnica tomada
    - risk_identified_by_user: Usuario identifico un riesgo
    - test_executed: Test ejecutado
    - deployment_completed: Deployment completado
    - incident_resolved: Incidente resuelto
    - security_scan_complete: Scan de seguridad completado
    """

    __tablename__ = "simulator_events"

    # Event metadata
    # FIX 3.2 Cortez3: Added ondelete="CASCADE" to prevent orphan records
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    # FIX Cortez69 HIGH-DB-001: Add activity_id with index for filtering events by activity
    activity_id = Column(String(100), nullable=True, index=True)
    simulator_type = Column(String(50), nullable=False, index=True)  # PO, SM, TI, IR, Client, DSO

    # Event details
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, default=dict)  # Datos especificos del evento
    timestamp = Column(DateTime, default=utc_now, nullable=False)

    # Context
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=True)  # info, warning, critical

    # Relationships
    session = relationship("SessionDB", back_populates="simulator_events")

    # Composite indexes
    __table_args__ = (
        # Query: Get all events for a session
        Index('idx_event_session', 'session_id', 'timestamp'),
        # Query: Get events by type for analysis
        Index('idx_event_type_student', 'event_type', 'student_id'),
        # Query: Get events by simulator
        Index('idx_event_simulator_session', 'simulator_type', 'session_id'),
        # FIX Cortez69 HIGH-DB-001: Query events by activity
        Index('idx_event_activity', 'activity_id', 'timestamp'),
        # FIX 2.13 Cortez6: Check constraint for valid simulator_type values
        # FIX Cortez21 DEFECTO 9.2: Added V2 simulators (senior_dev, qa_engineer, security_auditor, tech_lead, demanding_client)
        CheckConstraint(
            "simulator_type IN ('product_owner', 'scrum_master', 'tech_interviewer', 'incident_responder', 'client', 'devsecops', 'senior_dev', 'qa_engineer', 'security_auditor', 'tech_lead', 'demanding_client')",
            name='ck_simulator_event_type_valid'
        ),
    )
