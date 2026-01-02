"""
Institutional Repositories - Course reports, remediation plans, and risk alerts.

Cortez46: Extracted from repositories.py (5,134 lines)

SPRINT 5:
- HU-DOC-009: Reportes Institucionales
- HU-DOC-010: Gestión de Riesgos Institucionales
"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.core.constants import utc_now
from ..models import CourseReportDB, RemediationPlanDB, RiskAlertDB
from .base import BaseRepository

logger = logging.getLogger(__name__)


class CourseReportRepository(BaseRepository):
    """
    Repository for course-level aggregate reports.

    SPRINT 5 - HU-DOC-009: Reportes Institucionales
    """

    def create(
        self,
        course_id: str,
        teacher_id: str,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        summary_stats: dict,
        competency_distribution: dict,
        risk_distribution: dict,
        top_risks: Optional[List[dict]] = None,
        student_summaries: Optional[List[dict]] = None,
        institutional_recommendations: Optional[List[str]] = None,
        at_risk_students: Optional[List[str]] = None,
        format: str = "json",
        file_path: Optional[str] = None,
    ) -> CourseReportDB:
        """
        Create a new course report.

        Args:
            course_id: Course identifier (e.g., "PROG2_2025_1C")
            teacher_id: Teacher who generated the report
            report_type: Type of report (cohort_summary, risk_dashboard, etc.)
            period_start: Start of reporting period
            period_end: End of reporting period
            summary_stats: Aggregate statistics dict
            competency_distribution: Competency level distribution dict
            risk_distribution: Risk level distribution dict
            top_risks: Top 5 most frequent risks
            student_summaries: List of student summary dicts
            institutional_recommendations: Institutional recommendations
            at_risk_students: List of student IDs requiring intervention
            format: Export format (json, pdf, xlsx)
            file_path: Path to exported file

        Returns:
            Created CourseReportDB instance
        """
        report = CourseReportDB(
            id=str(uuid4()),
            course_id=course_id,
            teacher_id=teacher_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            summary_stats=summary_stats,
            competency_distribution=competency_distribution,
            risk_distribution=risk_distribution,
            top_risks=top_risks or [],
            student_summaries=student_summaries or [],
            institutional_recommendations=institutional_recommendations or [],
            at_risk_students=at_risk_students or [],
            format=format,
            file_path=file_path,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(
            "Course report created: %s for course %s",
            report.id,
            course_id,
            extra={
                "report_id": report.id,
                "course_id": course_id,
                "report_type": report_type,
                "teacher_id": teacher_id,
            },
        )
        return report

    def get_by_id(self, report_id: str) -> Optional[CourseReportDB]:
        """Get report by ID."""
        return self.db.query(CourseReportDB).filter(CourseReportDB.id == report_id).first()

    def get_by_course(
        self, course_id: str, limit: Optional[int] = None
    ) -> List[CourseReportDB]:
        """Get reports for a course ordered by period."""
        query = (
            self.db.query(CourseReportDB)
            .filter(CourseReportDB.course_id == course_id)
            .order_by(desc(CourseReportDB.period_start))
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_teacher(
        self, teacher_id: str, limit: Optional[int] = None
    ) -> List[CourseReportDB]:
        """Get reports by teacher ordered by period."""
        query = (
            self.db.query(CourseReportDB)
            .filter(CourseReportDB.teacher_id == teacher_id)
            .order_by(desc(CourseReportDB.period_start))
        )
        if limit:
            query = query.limit(limit)
        return query.all()

    def mark_exported(self, report_id: str, file_path: str) -> Optional[CourseReportDB]:
        """Mark report as exported with file path."""
        report = self.get_by_id(report_id)
        if not report:
            return None

        report.file_path = file_path
        report.exported_at = utc_now()
        report.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(report)

        logger.info(
            "Course report exported: %s to %s",
            report.id,
            file_path,
            extra={"report_id": report.id, "file_path": file_path},
        )
        return report


class RemediationPlanRepository(BaseRepository):
    """
    Repository for remediation plan operations.

    SPRINT 5 - HU-DOC-010: Gestión de Riesgos Institucionales
    """

    def create(
        self,
        student_id: str,
        teacher_id: str,
        plan_type: str,
        description: str,
        start_date: datetime,
        target_completion_date: datetime,
        activity_id: Optional[str] = None,
        trigger_risks: Optional[List[str]] = None,
        objectives: Optional[List[str]] = None,
        recommended_actions: Optional[List[dict]] = None,
    ) -> RemediationPlanDB:
        """
        Create a new remediation plan.

        Args:
            student_id: Target student ID
            teacher_id: Teacher creating the plan
            plan_type: Type of plan (tutoring, practice_exercises, etc.)
            description: Plan description
            start_date: Plan start date
            target_completion_date: Target completion date
            activity_id: Optional activity ID (null if general plan)
            trigger_risks: Risk IDs that triggered this plan
            objectives: List of specific objectives
            recommended_actions: List of action dicts

        Returns:
            Created RemediationPlanDB instance
        """
        plan = RemediationPlanDB(
            id=str(uuid4()),
            student_id=student_id,
            teacher_id=teacher_id,
            plan_type=plan_type,
            description=description,
            start_date=start_date,
            target_completion_date=target_completion_date,
            activity_id=activity_id,
            trigger_risks=trigger_risks or [],
            objectives=objectives or [],
            recommended_actions=recommended_actions or [],
            status="pending",
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        logger.info(
            "Remediation plan created: %s for student %s",
            plan.id,
            student_id,
            extra={
                "plan_id": plan.id,
                "student_id": student_id,
                "teacher_id": teacher_id,
                "plan_type": plan_type,
            },
        )
        return plan

    def get_by_id(self, plan_id: str) -> Optional[RemediationPlanDB]:
        """Get plan by ID."""
        return (
            self.db.query(RemediationPlanDB)
            .filter(RemediationPlanDB.id == plan_id)
            .first()
        )

    def get_by_student(
        self,
        student_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RemediationPlanDB]:
        """
        Get plans for student, optionally filtered by status.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        query = self.db.query(RemediationPlanDB).filter(
            RemediationPlanDB.student_id == student_id
        )
        if status:
            query = query.filter(RemediationPlanDB.status == status)
        return query.order_by(desc(RemediationPlanDB.start_date)).limit(limit).offset(offset).all()

    def get_by_teacher(
        self, teacher_id: str, status: Optional[str] = None
    ) -> List[RemediationPlanDB]:
        """Get plans by teacher, optionally filtered by status."""
        query = self.db.query(RemediationPlanDB).filter(
            RemediationPlanDB.teacher_id == teacher_id
        )
        if status:
            query = query.filter(RemediationPlanDB.status == status)
        return query.order_by(desc(RemediationPlanDB.target_completion_date)).all()

    def update_status(
        self,
        plan_id: str,
        status: str,
        progress_notes: Optional[str] = None,
        completion_evidence: Optional[List[str]] = None,
    ) -> Optional[RemediationPlanDB]:
        """Update plan status."""
        plan = self.get_by_id(plan_id)
        if not plan:
            return None

        plan.status = status
        if progress_notes:
            plan.progress_notes = progress_notes
        if completion_evidence:
            plan.completion_evidence = completion_evidence

        if status == "completed":
            plan.actual_completion_date = utc_now()

        plan.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(plan)

        logger.info(
            "Remediation plan status updated: %s to %s",
            plan.id,
            status,
            extra={"plan_id": plan.id, "status": status},
        )
        return plan

    def complete_plan(
        self,
        plan_id: str,
        outcome_evaluation: str,
        success_metrics: Optional[dict] = None,
    ) -> Optional[RemediationPlanDB]:
        """Complete a remediation plan with evaluation."""
        plan = self.get_by_id(plan_id)
        if not plan:
            return None

        plan.status = "completed"
        plan.actual_completion_date = utc_now()
        plan.outcome_evaluation = outcome_evaluation
        if success_metrics:
            plan.success_metrics = success_metrics

        plan.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(plan)

        logger.info(
            "Remediation plan completed: %s",
            plan.id,
            extra={"plan_id": plan.id, "success_metrics": success_metrics},
        )
        return plan


class RiskAlertRepository(BaseRepository):
    """
    Repository for institutional risk alert operations.

    SPRINT 5 - HU-DOC-010: Gestión de Riesgos Institucionales
    """

    def create(
        self,
        alert_type: str,
        severity: str,
        scope: str,
        title: str,
        description: str,
        detection_rule: str,
        student_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        course_id: Optional[str] = None,
        evidence: Optional[List[str]] = None,
        threshold_value: Optional[float] = None,
        actual_value: Optional[float] = None,
    ) -> RiskAlertDB:
        """
        Create a new risk alert.

        Args:
            alert_type: Type of alert (critical_risk_surge, ai_dependency_spike, etc.)
            severity: Severity level (low, medium, high, critical)
            scope: Scope (student, activity, course, institution)
            title: Alert title
            description: Alert description
            detection_rule: Rule that triggered the alert
            student_id: Student ID (if scope=student)
            activity_id: Activity ID (if scope=activity)
            course_id: Course ID (if scope=course)
            evidence: Links to risks, sessions, traces
            threshold_value: Threshold value for detection rule
            actual_value: Actual value that triggered the alert

        Returns:
            Created RiskAlertDB instance
        """
        alert = RiskAlertDB(
            id=str(uuid4()),
            alert_type=alert_type,
            severity=severity,
            scope=scope,
            title=title,
            description=description,
            detection_rule=detection_rule,
            student_id=student_id,
            activity_id=activity_id,
            course_id=course_id,
            evidence=evidence or [],
            threshold_value=threshold_value,
            actual_value=actual_value,
            status="open",
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)

        logger.warning(
            "Risk alert created: %s (%s)",
            alert_type,
            severity,
            extra={
                "alert_id": alert.id,
                "severity": severity,
                "scope": scope,
                "student_id": student_id,
            },
        )
        return alert

    def get_by_id(self, alert_id: str) -> Optional[RiskAlertDB]:
        """Get alert by ID."""
        return self.db.query(RiskAlertDB).filter(RiskAlertDB.id == alert_id).first()

    def get_by_student(
        self,
        student_id: str,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskAlertDB]:
        """
        Get alerts for student, optionally filtered by status.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        """
        query = self.db.query(RiskAlertDB).filter(
            RiskAlertDB.student_id == student_id
        )
        if status:
            query = query.filter(RiskAlertDB.status == status)
        return query.order_by(desc(RiskAlertDB.detected_at)).limit(limit).offset(offset).all()

    def get_by_course(
        self, course_id: str, status: Optional[str] = None
    ) -> List[RiskAlertDB]:
        """Get alerts for course, optionally filtered by status."""
        query = self.db.query(RiskAlertDB).filter(RiskAlertDB.course_id == course_id)
        if status:
            query = query.filter(RiskAlertDB.status == status)
        return query.order_by(desc(RiskAlertDB.detected_at)).all()

    def get_by_severity(
        self, severity: str, status: Optional[str] = "open"
    ) -> List[RiskAlertDB]:
        """Get alerts by severity level."""
        query = self.db.query(RiskAlertDB).filter(RiskAlertDB.severity == severity)
        if status:
            query = query.filter(RiskAlertDB.status == status)
        return query.order_by(desc(RiskAlertDB.detected_at)).all()

    def get_assigned_to(
        self, teacher_id: str, status: Optional[str] = None
    ) -> List[RiskAlertDB]:
        """Get alerts assigned to a teacher."""
        query = self.db.query(RiskAlertDB).filter(
            RiskAlertDB.assigned_to == teacher_id
        )
        if status:
            query = query.filter(RiskAlertDB.status == status)
        return query.order_by(desc(RiskAlertDB.detected_at)).all()

    def assign_to(self, alert_id: str, teacher_id: str) -> Optional[RiskAlertDB]:
        """Assign alert to a teacher."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        alert.assigned_to = teacher_id
        alert.assigned_at = utc_now()
        alert.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Risk alert assigned: %s to %s",
            alert.id,
            teacher_id,
            extra={"alert_id": alert.id, "assigned_to": teacher_id},
        )
        return alert

    def acknowledge(
        self, alert_id: str, acknowledged_by: str
    ) -> Optional[RiskAlertDB]:
        """Acknowledge an alert."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        alert.status = "acknowledged"
        alert.acknowledged_at = utc_now()
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Risk alert acknowledged: %s by %s",
            alert.id,
            acknowledged_by,
            extra={"alert_id": alert.id, "acknowledged_by": acknowledged_by},
        )
        return alert

    def resolve(
        self,
        alert_id: str,
        resolution_notes: str,
        remediation_plan_id: Optional[str] = None,
    ) -> Optional[RiskAlertDB]:
        """Resolve an alert."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        alert.status = "resolved"
        alert.resolution_notes = resolution_notes
        alert.resolved_at = utc_now()
        if remediation_plan_id:
            alert.remediation_plan_id = remediation_plan_id
        alert.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Risk alert resolved: %s",
            alert.id,
            extra={
                "alert_id": alert.id,
                "remediation_plan_id": remediation_plan_id,
            },
        )
        return alert

    def mark_false_positive(self, alert_id: str) -> Optional[RiskAlertDB]:
        """Mark alert as false positive."""
        alert = self.get_by_id(alert_id)
        if not alert:
            return None

        alert.status = "false_positive"
        alert.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(alert)

        logger.info(
            "Risk alert marked as false positive: %s",
            alert.id,
            extra={"alert_id": alert.id}
        )
        return alert
