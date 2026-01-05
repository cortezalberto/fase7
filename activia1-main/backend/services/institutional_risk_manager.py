"""
InstitutionalRiskManager - SPRINT 5 HU-DOC-010

Servicio para gestión proactiva de riesgos a nivel institucional.

Funcionalidades:
- Detección automática de alertas basadas en umbrales
- Creación de planes de remediación para estudiantes en riesgo
- Asignación de alertas a docentes
- Seguimiento de resolución de alertas
- Métricas de efectividad de intervenciones

Audiencia: Coordinadores, administradores, docentes
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database.models import (
    SessionDB,
    CognitiveTraceDB,
    RiskDB,
    EvaluationDB,
)
from ..database.repositories import (
    RiskAlertRepository,
    RemediationPlanRepository,
    RiskRepository,
)
from ..models.risk import RiskLevel, RiskDimension

logger = logging.getLogger(__name__)


class InstitutionalRiskManager:
    """
    Gestor de riesgos institucionales

    Monitorea patrones de riesgo a nivel estudiante, actividad, curso
    e institución, generando alertas automáticas y planes de remediación.
    """

    # Detection thresholds
    THRESHOLDS = {
        "ai_dependency_spike": 0.7,  # AI involvement > 0.7
        "critical_risk_surge": 2,  # 2+ critical risks in period
        "session_inactivity_days": 7,  # No sessions for 7 days
        "low_competency_threshold": 3.0,  # Overall score < 3.0/10
        "academic_integrity_threshold": 1,  # 1+ integrity risk
    }

    def __init__(
        self,
        db_session: Session,
        alert_repo: Optional[RiskAlertRepository] = None,
        plan_repo: Optional[RemediationPlanRepository] = None,
        risk_repo: Optional[RiskRepository] = None,
    ):
        """
        Initialize InstitutionalRiskManager

        Args:
            db_session: SQLAlchemy database session
            alert_repo: Repository for alerts (optional)
            plan_repo: Repository for remediation plans (optional)
            risk_repo: Repository for risks (optional)
        """
        self.db = db_session
        self.alert_repo = alert_repo or RiskAlertRepository(db_session)
        self.plan_repo = plan_repo or RemediationPlanRepository(db_session)
        self.risk_repo = risk_repo or RiskRepository(db_session)

    def scan_for_alerts(
        self,
        student_ids: Optional[List[str]] = None,
        activity_ids: Optional[List[str]] = None,
        course_ids: Optional[List[str]] = None,
        lookback_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Scan for risk alerts based on detection rules

        FIX Cortez70 CRIT-SVC-001: Refactored to use batch loading instead of N+1 queries.
        Previously executed 5N-10N queries for N students. Now executes ~10 queries total.

        Args:
            student_ids: Specific students to scan (None = all)
            activity_ids: Specific activities to scan (None = all)
            course_ids: Specific courses to scan (None = all)
            lookback_days: Days to look back for analysis

        Returns:
            List of created alerts
        """
        logger.info(
            "Scanning for risk alerts",
            extra={
                "student_count": len(student_ids) if student_ids else "all",
                "lookback_days": lookback_days,
            },
        )

        alerts_created = []
        period_start = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        # Get students to scan
        if student_ids is None:
            # Get all active students (with sessions in period)
            student_ids = [
                s[0]
                for s in self.db.query(SessionDB.student_id)
                .filter(SessionDB.start_time >= period_start)
                .distinct()
                .all()
            ]

        if not student_ids:
            return []

        # FIX Cortez70 CRIT-SVC-001: Batch load all required data upfront
        # 1. AI dependency: Average ai_involvement per student
        ai_dependency_data = dict(
            self.db.query(
                CognitiveTraceDB.student_id,
                func.avg(CognitiveTraceDB.ai_involvement)
            )
            .filter(
                CognitiveTraceDB.student_id.in_(student_ids),
                CognitiveTraceDB.created_at >= period_start,
            )
            .group_by(CognitiveTraceDB.student_id)
            .all()
        )

        # 2. Critical risks: Count per student
        critical_risks_data = {}
        critical_risks_query = (
            self.db.query(RiskDB.student_id, RiskDB.id)
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.risk_level == "critical",
                RiskDB.created_at >= period_start,
            )
            .all()
        )
        for student_id, risk_id in critical_risks_query:
            if student_id not in critical_risks_data:
                critical_risks_data[student_id] = []
            critical_risks_data[student_id].append(risk_id)

        # 3. Ethical risks: Count per student
        ethical_risks_data = {}
        ethical_risks_query = (
            self.db.query(RiskDB.student_id, RiskDB.id)
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.dimension == "ethical",
                RiskDB.created_at >= period_start,
            )
            .all()
        )
        for student_id, risk_id in ethical_risks_query:
            if student_id not in ethical_risks_data:
                ethical_risks_data[student_id] = []
            ethical_risks_data[student_id].append(risk_id)

        # 4. Last sessions: For inactivity check
        last_sessions_data = dict(
            self.db.query(
                SessionDB.student_id,
                func.max(SessionDB.start_time)
            )
            .filter(SessionDB.student_id.in_(student_ids))
            .group_by(SessionDB.student_id)
            .all()
        )

        # 5. Latest evaluations: For competency check
        # Subquery to get latest evaluation per student
        from sqlalchemy import desc
        latest_evals = {}
        for student_id in student_ids:
            eval_result = (
                self.db.query(EvaluationDB.overall_score, EvaluationDB.id)
                .filter(
                    EvaluationDB.student_id == student_id,
                    EvaluationDB.created_at >= period_start,
                )
                .order_by(desc(EvaluationDB.created_at))
                .first()
            )
            if eval_result:
                latest_evals[student_id] = eval_result

        # Now process each student using preloaded data (no additional queries)
        for student_id in student_ids:
            # AI Dependency Spike
            avg_ai = ai_dependency_data.get(student_id, 0.0) or 0.0
            if avg_ai > self.THRESHOLDS["ai_dependency_spike"]:
                alert = self._create_ai_dependency_alert(student_id, float(avg_ai))
                if alert:
                    alerts_created.append(alert)

            # Critical Risk Surge
            critical_risk_ids = critical_risks_data.get(student_id, [])
            if len(critical_risk_ids) >= self.THRESHOLDS["critical_risk_surge"]:
                alert = self._create_critical_surge_alert(student_id, critical_risk_ids)
                if alert:
                    alerts_created.append(alert)

            # Academic Integrity
            ethical_risk_ids = ethical_risks_data.get(student_id, [])
            if len(ethical_risk_ids) >= self.THRESHOLDS["academic_integrity_threshold"]:
                alert = self._create_integrity_alert(student_id, ethical_risk_ids)
                if alert:
                    alerts_created.append(alert)

            # Session Inactivity
            last_session_time = last_sessions_data.get(student_id)
            if last_session_time:
                # FIX Cortez70 CRIT-SVC-002: Ensure timezone-aware comparison
                if last_session_time.tzinfo is None:
                    last_session_time = last_session_time.replace(tzinfo=timezone.utc)
                cutoff_date = datetime.now(timezone.utc) - timedelta(
                    days=self.THRESHOLDS["session_inactivity_days"]
                )
                if last_session_time < cutoff_date:
                    days_inactive = (datetime.now(timezone.utc) - last_session_time).days
                    alert = self._create_inactivity_alert(student_id, days_inactive)
                    if alert:
                        alerts_created.append(alert)

            # Low Competency
            eval_data = latest_evals.get(student_id)
            if eval_data and eval_data[0] < self.THRESHOLDS["low_competency_threshold"]:
                alert = self._create_low_competency_alert(
                    student_id, eval_data[0], eval_data[1]
                )
                if alert:
                    alerts_created.append(alert)

        logger.info(
            "Alert scan completed",
            extra={
                "alerts_created": len(alerts_created),
                "students_scanned": len(student_ids),
            },
        )
        return alerts_created

    # FIX Cortez70 CRIT-SVC-001: Helper methods for alert creation (factored from checks)
    def _create_ai_dependency_alert(
        self, student_id: str, avg_ai: float
    ) -> Optional[Dict[str, Any]]:
        """Create AI dependency spike alert."""
        threshold = self.THRESHOLDS["ai_dependency_spike"]
        alert = self.alert_repo.create(
            alert_type="ai_dependency_spike",
            severity="high",
            scope="student",
            student_id=student_id,
            title=f"Alta dependencia de IA detectada: {student_id}",
            description=f"El estudiante presenta un promedio de dependencia de IA de {avg_ai:.2f} (umbral: {threshold})",
            detection_rule=f"ai_dependency > {threshold}",
            threshold_value=threshold,
            actual_value=avg_ai,
            evidence=[],
        )
        logger.warning(
            "AI dependency spike detected",
            extra={"student_id": student_id, "avg_ai_dependency": avg_ai, "alert_id": alert.id},
        )
        return {
            "alert_id": alert.id,
            "student_id": student_id,
            "alert_type": "ai_dependency_spike",
            "severity": "high",
            "actual_value": avg_ai,
        }

    def _create_critical_surge_alert(
        self, student_id: str, risk_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Create critical risk surge alert."""
        threshold = self.THRESHOLDS["critical_risk_surge"]
        alert = self.alert_repo.create(
            alert_type="critical_risk_surge",
            severity="critical",
            scope="student",
            student_id=student_id,
            title=f"Multiples riesgos criticos: {student_id}",
            description=f"El estudiante presenta {len(risk_ids)} riesgos criticos (umbral: {threshold})",
            detection_rule=f"critical_risks >= {threshold}",
            threshold_value=float(threshold),
            actual_value=float(len(risk_ids)),
            evidence=risk_ids,
        )
        logger.critical(
            "Critical risk surge detected",
            extra={"student_id": student_id, "critical_risks_count": len(risk_ids), "alert_id": alert.id},
        )
        return {
            "alert_id": alert.id,
            "student_id": student_id,
            "alert_type": "critical_risk_surge",
            "severity": "critical",
            "actual_value": len(risk_ids),
        }

    def _create_integrity_alert(
        self, student_id: str, risk_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Create academic integrity alert."""
        threshold = self.THRESHOLDS["academic_integrity_threshold"]
        alert = self.alert_repo.create(
            alert_type="academic_integrity",
            severity="high",
            scope="student",
            student_id=student_id,
            title=f"Riesgo de integridad academica: {student_id}",
            description=f"Detectados {len(risk_ids)} riesgos eticos/integridad",
            detection_rule=f"ethical_risks >= {threshold}",
            threshold_value=float(threshold),
            actual_value=float(len(risk_ids)),
            evidence=risk_ids,
        )
        logger.warning(
            "Academic integrity risk detected",
            extra={"student_id": student_id, "integrity_risks_count": len(risk_ids), "alert_id": alert.id},
        )
        return {
            "alert_id": alert.id,
            "student_id": student_id,
            "alert_type": "academic_integrity",
            "severity": "high",
            "actual_value": len(risk_ids),
        }

    def _create_inactivity_alert(
        self, student_id: str, days_inactive: int
    ) -> Optional[Dict[str, Any]]:
        """Create session inactivity alert."""
        threshold_days = self.THRESHOLDS["session_inactivity_days"]
        alert = self.alert_repo.create(
            alert_type="session_inactivity",
            severity="medium",
            scope="student",
            student_id=student_id,
            title=f"Inactividad prolongada: {student_id}",
            description=f"El estudiante lleva {days_inactive} dias sin sesiones (umbral: {threshold_days} dias)",
            detection_rule=f"days_since_last_session >= {threshold_days}",
            threshold_value=float(threshold_days),
            actual_value=float(days_inactive),
            evidence=[],
        )
        logger.info(
            "Session inactivity detected",
            extra={"student_id": student_id, "days_inactive": days_inactive, "alert_id": alert.id},
        )
        return {
            "alert_id": alert.id,
            "student_id": student_id,
            "alert_type": "session_inactivity",
            "severity": "medium",
            "actual_value": days_inactive,
        }

    def _create_low_competency_alert(
        self, student_id: str, score: float, eval_id: str
    ) -> Optional[Dict[str, Any]]:
        """Create low competency alert."""
        threshold = self.THRESHOLDS["low_competency_threshold"]
        alert = self.alert_repo.create(
            alert_type="low_competency",
            severity="medium",
            scope="student",
            student_id=student_id,
            title=f"Competencia baja detectada: {student_id}",
            description=f"Evaluacion con puntaje {score}/10 (umbral: {threshold})",
            detection_rule=f"overall_score < {threshold}",
            threshold_value=threshold,
            actual_value=score,
            evidence=[eval_id],
        )
        logger.warning(
            "Low competency detected",
            extra={"student_id": student_id, "overall_score": score, "alert_id": alert.id},
        )
        return {
            "alert_id": alert.id,
            "student_id": student_id,
            "alert_type": "low_competency",
            "severity": "medium",
            "actual_value": score,
        }

    def create_remediation_plan(
        self,
        student_id: str,
        teacher_id: str,
        trigger_risk_ids: List[str],
        plan_type: str,
        description: str,
        objectives: List[str],
        recommended_actions: List[Dict[str, Any]],
        activity_id: Optional[str] = None,
        duration_days: int = 14,
    ) -> Dict[str, Any]:
        """
        Create a remediation plan for a student

        Args:
            student_id: Student ID
            teacher_id: Teacher creating the plan
            trigger_risk_ids: Risk IDs that triggered this plan
            plan_type: Type of plan (tutoring, practice_exercises, etc.)
            description: Plan description
            objectives: List of objectives
            recommended_actions: List of actions with deadlines
            activity_id: Optional activity ID
            duration_days: Plan duration in days (default: 14)

        Returns:
            Created plan data
        """
        start_date = datetime.now(timezone.utc)
        target_completion = start_date + timedelta(days=duration_days)

        plan = self.plan_repo.create(
            student_id=student_id,
            teacher_id=teacher_id,
            plan_type=plan_type,
            description=description,
            start_date=start_date,
            target_completion_date=target_completion,
            activity_id=activity_id,
            trigger_risks=trigger_risk_ids,
            objectives=objectives,
            recommended_actions=recommended_actions,
        )

        logger.info(
            "Remediation plan created",
            extra={
                "plan_id": plan.id,
                "student_id": student_id,
                "teacher_id": teacher_id,
                "duration_days": duration_days,
            },
        )

        return {
            "plan_id": plan.id,
            "student_id": student_id,
            "teacher_id": teacher_id,
            "plan_type": plan_type,
            "description": description,
            "start_date": start_date.isoformat(),
            "target_completion_date": target_completion.isoformat(),
            "objectives": objectives,
            "recommended_actions": recommended_actions,
            "status": "pending",
        }

    def assign_alert(self, alert_id: str, teacher_id: str) -> Dict[str, Any]:
        """
        Assign an alert to a teacher

        Args:
            alert_id: Alert ID
            teacher_id: Teacher to assign to

        Returns:
            Updated alert data
        """
        alert = self.alert_repo.assign_to(alert_id, teacher_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        logger.info(
            "Alert assigned",
            extra={"alert_id": alert_id, "teacher_id": teacher_id},
        )

        return {
            "alert_id": alert.id,
            "assigned_to": alert.assigned_to,
            "assigned_at": alert.assigned_at.isoformat() if alert.assigned_at else None,
            "status": alert.status,
        }

    def acknowledge_alert(self, alert_id: str, teacher_id: str) -> Dict[str, Any]:
        """
        Acknowledge an alert (teacher has seen it)

        Args:
            alert_id: Alert ID
            teacher_id: Teacher acknowledging

        Returns:
            Updated alert data
        """
        alert = self.alert_repo.acknowledge(alert_id, teacher_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        logger.info(
            "Alert acknowledged",
            extra={"alert_id": alert_id, "teacher_id": teacher_id},
        )

        return {
            "alert_id": alert.id,
            "acknowledged_by": alert.acknowledged_by,
            "acknowledged_at": alert.acknowledged_at.isoformat()
            if alert.acknowledged_at
            else None,
            "status": alert.status,
        }

    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: str,
        remediation_plan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve an alert

        Args:
            alert_id: Alert ID
            resolution_notes: Notes on resolution
            remediation_plan_id: Optional plan ID if plan was created

        Returns:
            Updated alert data
        """
        alert = self.alert_repo.resolve(alert_id, resolution_notes, remediation_plan_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        logger.info(
            "Alert resolved",
            extra={
                "alert_id": alert_id,
                "remediation_plan_id": remediation_plan_id,
            },
        )

        return {
            "alert_id": alert.id,
            "status": alert.status,
            "resolution_notes": alert.resolution_notes,
            "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
            "remediation_plan_id": alert.remediation_plan_id,
        }

    def get_dashboard_metrics(
        self, teacher_id: Optional[str] = None, course_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get dashboard metrics for risk management

        FIX Cortez81: Updated to return structure expected by frontend RiskDashboard interface

        Args:
            teacher_id: Filter by teacher (optional)
            course_id: Filter by course (optional)

        Returns:
            Dashboard metrics matching frontend RiskDashboard interface
        """
        from ..database.models import RiskAlertDB, RemediationPlanDB
        from sqlalchemy import or_, desc

        # Base query for alerts
        base_query = self.db.query(RiskAlertDB)
        if teacher_id:
            base_query = base_query.filter(
                or_(
                    RiskAlertDB.assigned_to == teacher_id,
                    RiskAlertDB.assigned_to.is_(None),
                )
            )

        # Summary counts
        total_alerts = base_query.count()
        pending_alerts = base_query.filter(RiskAlertDB.status == "pending").count()
        critical_alerts = base_query.filter(RiskAlertDB.severity == "critical").count()

        # Resolved this week
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        resolved_this_week = (
            base_query.filter(
                RiskAlertDB.status == "resolved",
                RiskAlertDB.resolved_at >= seven_days_ago,
            ).count()
        )

        # Alerts by severity
        alerts_by_severity = {
            "critical": base_query.filter(RiskAlertDB.severity == "critical").count(),
            "high": base_query.filter(RiskAlertDB.severity == "high").count(),
            "medium": base_query.filter(RiskAlertDB.severity == "medium").count(),
            "low": base_query.filter(RiskAlertDB.severity == "low").count(),
        }

        # Alerts by type
        alert_types_query = (
            self.db.query(RiskAlertDB.alert_type, func.count(RiskAlertDB.id))
            .group_by(RiskAlertDB.alert_type)
            .all()
        )
        alerts_by_type = {alert_type: count for alert_type, count in alert_types_query}

        # Recent alerts (last 10)
        recent_alerts_db = (
            base_query
            .order_by(desc(RiskAlertDB.detected_at))
            .limit(10)
            .all()
        )
        recent_alerts = [
            {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "scope": alert.scope,
                "title": alert.title,
                "description": alert.description,
                "affected_students": [alert.student_id] if alert.student_id else [],
                "affected_activities": [alert.activity_id] if alert.activity_id else [],
                "evidence": alert.evidence or [],
                "recommendations": [],
                "status": alert.status,
                "assigned_to": alert.assigned_to,
                "created_at": alert.detected_at.isoformat() if alert.detected_at else None,
                "updated_at": alert.updated_at.isoformat() if alert.updated_at else None,
            }
            for alert in recent_alerts_db
        ]

        # Trends (last 7 days)
        trends = []
        for i in range(7):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            created = self.db.query(RiskAlertDB).filter(
                RiskAlertDB.detected_at >= day_start,
                RiskAlertDB.detected_at < day_end,
            ).count()

            resolved = self.db.query(RiskAlertDB).filter(
                RiskAlertDB.resolved_at >= day_start,
                RiskAlertDB.resolved_at < day_end,
            ).count()

            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "alerts_created": created,
                "alerts_resolved": resolved,
            })

        trends.reverse()  # Oldest first

        return {
            "summary": {
                "total_alerts": total_alerts,
                "pending_alerts": pending_alerts,
                "critical_alerts": critical_alerts,
                "resolved_this_week": resolved_this_week,
            },
            "alerts_by_severity": alerts_by_severity,
            "alerts_by_type": alerts_by_type,
            "recent_alerts": recent_alerts,
            "trends": trends,
        }

    # FIX Cortez70: Removed deprecated _check_* methods (lines 656-895)
    # These were replaced by batch-loading approach with _create_* helper methods
    # See scan_for_alerts() for the new implementation that reduces N+1 queries
