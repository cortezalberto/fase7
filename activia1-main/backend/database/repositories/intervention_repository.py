"""
Intervention Repository - Teacher intervention database operations.

Cortez82: Created for persistencia de reconocimiento de alertas (Mejora 4.1)

Provides:
- InterventionRepository: CRUD operations for teacher interventions
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from sqlalchemy.exc import SQLAlchemyError

from ..models.teacher_intervention import TeacherInterventionDB

logger = logging.getLogger(__name__)


class InterventionRepository:
    """Repository for teacher intervention operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(
        self,
        teacher_id: str,
        student_id: str,
        intervention_type: str = "alert_acknowledgment",
        session_id: Optional[str] = None,
        alert_id: Optional[str] = None,
        notes: Optional[str] = None,
        action_taken: Optional[str] = None,
        alert_context: Optional[Dict[str, Any]] = None,
    ) -> TeacherInterventionDB:
        """
        Create a new teacher intervention.

        Args:
            teacher_id: ID of the teacher making the intervention
            student_id: ID of the student being helped
            intervention_type: Type of intervention
            session_id: Optional session ID
            alert_id: Optional alert ID being acknowledged
            notes: Teacher's notes
            action_taken: Description of action taken
            alert_context: Original alert data for historical reference

        Returns:
            Created TeacherInterventionDB instance
        """
        db_intervention = TeacherInterventionDB(
            id=str(uuid4()),
            teacher_id=teacher_id,
            student_id=student_id,
            session_id=session_id,
            alert_id=alert_id,
            intervention_type=intervention_type,
            notes=notes,
            action_taken=action_taken,
            status="acknowledged",
        )

        # Handle alert_context separately due to JSONB
        if alert_context:
            db_intervention.alert_context = alert_context

        # FIX Cortez83: Use commit() instead of flush() to persist data
        try:
            self.db.add(db_intervention)
            self.db.commit()
            self.db.refresh(db_intervention)

            logger.info(
                "Teacher intervention created",
                extra={
                    "intervention_id": db_intervention.id,
                    "teacher_id": teacher_id,
                    "student_id": student_id,
                    "type": intervention_type,
                }
            )

            return db_intervention
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create intervention: %s", str(e), exc_info=True)
            raise

    def get_by_id(self, intervention_id: str) -> Optional[TeacherInterventionDB]:
        """Get intervention by ID."""
        return (
            self.db.query(TeacherInterventionDB)
            .filter(TeacherInterventionDB.id == intervention_id)
            .first()
        )

    def get_by_teacher(
        self,
        teacher_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TeacherInterventionDB]:
        """
        Get interventions by teacher.

        Args:
            teacher_id: Teacher ID
            status: Optional status filter
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            List of interventions
        """
        query = (
            self.db.query(TeacherInterventionDB)
            .filter(TeacherInterventionDB.teacher_id == teacher_id)
        )

        if status:
            query = query.filter(TeacherInterventionDB.status == status)

        return (
            query
            .order_by(desc(TeacherInterventionDB.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_student(
        self,
        student_id: str,
        limit: int = 50
    ) -> List[TeacherInterventionDB]:
        """Get all interventions for a student."""
        return (
            self.db.query(TeacherInterventionDB)
            .filter(TeacherInterventionDB.student_id == student_id)
            .order_by(desc(TeacherInterventionDB.created_at))
            .limit(limit)
            .all()
        )

    def get_by_alert(self, alert_id: str) -> Optional[TeacherInterventionDB]:
        """Get intervention for a specific alert."""
        return (
            self.db.query(TeacherInterventionDB)
            .filter(TeacherInterventionDB.alert_id == alert_id)
            .first()
        )

    def is_alert_acknowledged(self, alert_id: str) -> bool:
        """Check if an alert has been acknowledged."""
        return self.get_by_alert(alert_id) is not None

    def get_acknowledged_alert_ids(self, alert_ids: List[str]) -> List[str]:
        """
        Batch check which alerts have been acknowledged.

        Args:
            alert_ids: List of alert IDs to check

        Returns:
            List of alert IDs that have been acknowledged
        """
        if not alert_ids:
            return []

        results = (
            self.db.query(TeacherInterventionDB.alert_id)
            .filter(TeacherInterventionDB.alert_id.in_(alert_ids))
            .all()
        )

        return [r[0] for r in results if r[0]]

    def update_status(
        self,
        intervention_id: str,
        status: str,
        resolution_notes: Optional[str] = None
    ) -> Optional[TeacherInterventionDB]:
        """
        Update intervention status.

        Args:
            intervention_id: Intervention ID
            status: New status
            resolution_notes: Optional resolution notes

        Returns:
            Updated intervention or None if not found
        """
        # FIX Cortez83: Use commit() with try/except instead of flush()
        try:
            intervention = self.get_by_id(intervention_id)
            if not intervention:
                return None

            intervention.status = status
            intervention.updated_at = datetime.now(timezone.utc)

            if status in ("resolved", "closed") and resolution_notes:
                intervention.resolution_notes = resolution_notes
                intervention.resolved_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(intervention)
            return intervention
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to update intervention status: %s", str(e), exc_info=True)
            raise

    def count_by_teacher(
        self,
        teacher_id: str,
        status: Optional[str] = None
    ) -> int:
        """Count interventions by teacher with optional status filter."""
        query = (
            self.db.query(TeacherInterventionDB)
            .filter(TeacherInterventionDB.teacher_id == teacher_id)
        )

        if status:
            query = query.filter(TeacherInterventionDB.status == status)

        return query.count()

    def get_pending_for_student(
        self,
        student_id: str
    ) -> List[TeacherInterventionDB]:
        """Get pending (non-resolved) interventions for a student."""
        return (
            self.db.query(TeacherInterventionDB)
            .filter(
                TeacherInterventionDB.student_id == student_id,
                TeacherInterventionDB.status.in_(["acknowledged", "in_progress"])
            )
            .order_by(desc(TeacherInterventionDB.created_at))
            .all()
        )
