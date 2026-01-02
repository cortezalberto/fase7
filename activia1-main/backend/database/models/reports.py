"""
Reports Models - Course reports, remediation plans, and risk alerts.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- CourseReportDB: Course-level aggregate reports
- RemediationPlanDB: Student remediation plans
- RiskAlertDB: Institutional risk alerts
"""
from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime,
    ForeignKey, JSON, Index, CheckConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, utc_now


class CourseReportDB(Base, BaseModel):
    """
    Database model for Course-level aggregate reports

    SPRINT 5 - HU-DOC-009: Reportes Institucionales
    Almacena reportes generados por docentes para analisis de cohortes completas.
    """

    __tablename__ = "course_reports"

    # Report identification
    course_id = Column(String(100), nullable=False, index=True)  # e.g., "PROG2_2025_1C"
    # FIX 1.1 Cortez6: Added FK constraint to users table
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    report_type = Column(String(50), nullable=False)  # "cohort_summary", "risk_dashboard", "competency_distribution"

    # Time period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Aggregate data (JSON for flexibility)
    summary_stats = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "total_students": 45,
    #   "total_sessions": 320,
    #   "total_interactions": 1842,
    #   "avg_ai_dependency": 0.42
    # }

    competency_distribution = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "AVANZADO": 12,
    #   "INTERMEDIO": 25,
    #   "BASICO": 8
    # }

    risk_distribution = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "CRITICAL": 3,
    #   "HIGH": 8,
    #   "MEDIUM": 15,
    #   "LOW": 7
    # }

    top_risks = Column(JSON, default=list)  # Top 5 riesgos mas frecuentes

    # Student-level aggregates
    student_summaries = Column(JSON, default=list)
    # List of:
    # {
    #   "student_id": "...",
    #   "sessions": 7,
    #   "ai_dependency": 0.45,
    #   "competency": "INTERMEDIO",
    #   "risks": 2
    # }

    # Recommendations
    institutional_recommendations = Column(JSON, default=list)
    at_risk_students = Column(JSON, default=list)  # Students requiring intervention

    # Export metadata
    format = Column(String(20), default="json")  # json, pdf, xlsx
    file_path = Column(String(500), nullable=True)  # Path to exported file
    exported_at = Column(DateTime, nullable=True)

    # FIX 1.1 Cortez6: Added relationship to teacher
    # FIX 3.1 Cortez7: Added back_populates for bidirectional relationship
    teacher = relationship("UserDB", back_populates="course_reports", foreign_keys=[teacher_id])

    # Composite indexes
    __table_args__ = (
        # Query: Get reports by teacher ordered by period
        Index('idx_report_teacher_period', 'teacher_id', 'period_start'),
        # Query: Get course reports by type
        Index('idx_report_course_type', 'course_id', 'report_type'),
        # Query: Get recent reports
        Index('idx_report_created', 'created_at'),
        # FIX 5.2 Cortez6: Added composite index for teacher + course
        Index('idx_report_teacher_course', 'teacher_id', 'course_id'),
    )


class RemediationPlanDB(Base, BaseModel):
    """
    Database model for student remediation plans

    SPRINT 5 - HU-DOC-010: Gestion de Riesgos Institucionales
    Planes de remediacion creados por docentes para estudiantes en riesgo.
    """

    __tablename__ = "remediation_plans"

    # Target student
    student_id = Column(String(100), nullable=False, index=True)
    activity_id = Column(String(100), nullable=True)  # Nullable: plan puede ser general
    # FIX 1.2 Cortez6: Added FK constraint to users table
    teacher_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Trigger risks (que motivaron el plan)
    trigger_risks = Column(JSON, default=list)  # List of Risk IDs

    # Plan details
    plan_type = Column(String(50), nullable=False)  # "tutoring", "practice_exercises", "conceptual_review", "policy_clarification"
    description = Column(Text, nullable=False)  # Descripcion del plan
    objectives = Column(JSON, default=list)  # Objetivos especificos

    # Actions
    recommended_actions = Column(JSON, default=list)
    # List of:
    # {
    #   "action_type": "tutoring_session",
    #   "description": "Sesion de tutoria sobre...",
    #   "deadline": "2025-12-15",
    #   "status": "pending"
    # }

    # Timeline
    start_date = Column(DateTime, nullable=False)
    target_completion_date = Column(DateTime, nullable=False)
    actual_completion_date = Column(DateTime, nullable=True)

    # Progress tracking
    status = Column(String(20), default="pending")  # pending, in_progress, completed, cancelled
    progress_notes = Column(Text, nullable=True)
    completion_evidence = Column(JSON, default=list)  # Links to completed actions

    # Outcomes
    outcome_evaluation = Column(Text, nullable=True)  # Evaluacion final del docente
    success_metrics = Column(JSON, nullable=True)
    # {
    #   "ai_dependency_before": 0.75,
    #   "ai_dependency_after": 0.45,
    #   "risks_resolved": 3
    # }

    # FIX 1.5 Cortez5: Add back_populates relationship to RiskAlertDB
    risk_alerts = relationship(
        "RiskAlertDB",
        back_populates="remediation_plan",
        foreign_keys="RiskAlertDB.remediation_plan_id"
    )
    # FIX 1.2 Cortez6: Added relationship to teacher
    # FIX 3.2 Cortez7: Added back_populates for bidirectional relationship
    teacher = relationship("UserDB", back_populates="remediation_plans_created", foreign_keys=[teacher_id])

    # Composite indexes
    __table_args__ = (
        # Query: Get plans for student by status
        Index('idx_plan_student_status', 'student_id', 'status'),
        # Query: Get plans by teacher ordered by deadline
        Index('idx_plan_teacher_deadline', 'teacher_id', 'target_completion_date'),
        # Query: Get active plans
        Index('idx_plan_status_start', 'status', 'start_date'),
        # FIX 4.1 Cortez7: Index for actual_completion_date timestamp queries
        Index('idx_plan_completion_date', 'actual_completion_date'),
        # FIX 2.7 Cortez6: Check constraint for valid plan_type values
        CheckConstraint(
            "plan_type IN ('tutoring', 'practice_exercises', 'conceptual_review', 'policy_clarification')",
            name='ck_plan_type_valid'
        ),
        # FIX 2.8 Cortez6: Check constraint for valid status values
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'cancelled')",
            name='ck_remediation_status_valid'
        ),
    )


class RiskAlertDB(Base, BaseModel):
    """
    Database model for institutional risk alerts

    SPRINT 5 - HU-DOC-010: Gestion de Riesgos Institucionales
    Alertas automaticas generadas cuando se detectan patrones de riesgo institucionales.
    """

    __tablename__ = "risk_alerts"

    # Alert metadata
    alert_type = Column(String(50), nullable=False)  # "critical_risk_surge", "ai_dependency_spike", "academic_integrity", "pattern_anomaly"
    severity = Column(String(20), nullable=False)  # "low", "medium", "high", "critical"
    scope = Column(String(20), nullable=False)  # "student", "activity", "course", "institution"

    # Scope identifiers
    student_id = Column(String(100), nullable=True, index=True)
    activity_id = Column(String(100), nullable=True, index=True)
    course_id = Column(String(100), nullable=True, index=True)

    # Alert details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, default=list)  # Links to risks, sessions, traces

    # Detection
    detected_at = Column(DateTime, default=utc_now, nullable=False)
    detection_rule = Column(String(100), nullable=False)  # e.g., "ai_dependency > 0.7 for 3+ sessions"
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)

    # Assignment
    # FIX 1.3 Cortez6: Added FK constraint to users table
    assigned_to = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)

    # Resolution
    status = Column(String(20), default="open")  # open, acknowledged, investigating, resolved, false_positive
    acknowledged_at = Column(DateTime, nullable=True)
    # FIX 1.4 Cortez6: Added FK constraint to users table
    # FIX Cortez20: Added index=True for FK performance
    acknowledged_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    # FIX 3.3 Cortez3: Added ondelete="SET NULL" to maintain alerts when plan is deleted
    # FIX Cortez20: Added index=True for FK performance
    remediation_plan_id = Column(String(36), ForeignKey("remediation_plans.id", ondelete="SET NULL"), nullable=True, index=True)

    # FIX 1.5 Cortez5: Updated relationship with back_populates
    remediation_plan = relationship(
        "RemediationPlanDB",
        back_populates="risk_alerts",
        foreign_keys=[remediation_plan_id]
    )
    # FIX 1.3 Cortez6: Added relationship to assigned user
    # FIX 3.3 Cortez7: Added back_populates for bidirectional relationship
    assigned_to_user = relationship("UserDB", back_populates="assigned_alerts", foreign_keys=[assigned_to])
    # FIX 1.4 Cortez6: Added relationship to acknowledger
    # FIX 3.3 Cortez7: Added back_populates for bidirectional relationship
    acknowledged_by_user = relationship("UserDB", back_populates="acknowledged_alerts", foreign_keys=[acknowledged_by])

    # Composite indexes
    __table_args__ = (
        # Query: Get open alerts by severity
        Index('idx_alert_status_severity', 'status', 'severity'),
        # Query: Get alerts for student
        Index('idx_alert_student_status', 'student_id', 'status'),
        # Query: Get alerts by course ordered by detection time
        Index('idx_alert_course_detected', 'course_id', 'detected_at'),
        # Query: Get assigned alerts for a teacher
        Index('idx_alert_assigned_status', 'assigned_to', 'status'),
        # FIX 4.1 Cortez7: Index for resolved_at timestamp queries
        Index('idx_alert_resolved_at', 'resolved_at'),
        # FIX 2.9 Cortez6: Check constraint for valid alert_type values
        CheckConstraint(
            "alert_type IN ('critical_risk_surge', 'ai_dependency_spike', 'academic_integrity', 'pattern_anomaly')",
            name='ck_alert_type_valid'
        ),
        # FIX 2.10 Cortez6: Check constraint for valid severity values
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name='ck_alert_severity_valid'
        ),
        # FIX 2.11 Cortez6: Check constraint for valid scope values
        CheckConstraint(
            "scope IN ('student', 'activity', 'course', 'institution')",
            name='ck_alert_scope_valid'
        ),
        # FIX 2.12 Cortez6: Check constraint for valid status values
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'investigating', 'resolved', 'false_positive')",
            name='ck_alert_status_valid'
        ),
    )
