"""
Session Repository - Learning session database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- SessionRepository: CRUD operations for learning sessions
- Eager loading support to prevent N+1 queries
- Batch loading for multiple sessions
- Pessimistic locking for concurrent updates
"""
from typing import List, Optional, Dict
from uuid import uuid4
import logging

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, select, exists
from sqlalchemy.exc import SQLAlchemyError

from backend.core.constants import utc_now
from ..models import (
    SessionDB,
    CognitiveTraceDB,
    RiskDB,
    EvaluationDB,
    GitTraceDB,
    InterviewSessionDB,
    IncidentSimulationDB,
)

logger = logging.getLogger(__name__)


class SessionRepository:
    """Repository for session operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(
        self,
        student_id: str,
        activity_id: str,
        mode: str = "TUTOR",
        simulator_type: Optional[str] = None,
    ) -> SessionDB:
        """
        Create a new learning session.

        Args:
            student_id: Student identifier
            activity_id: Activity identifier
            mode: Session mode (TUTOR, EVALUATOR, SIMULATOR, RISK_ANALYST)
            simulator_type: Type of simulator when mode=SIMULATOR

        Returns:
            Created SessionDB instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            session = SessionDB(
                id=str(uuid4()),
                student_id=student_id,
                activity_id=activity_id,
                mode=mode,
                simulator_type=simulator_type,
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            return session
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Failed to create session: %s", str(e), exc_info=True)
            raise

    def get_by_id(self, session_id: str, load_relations: bool = False) -> Optional[SessionDB]:
        """
        Get session by ID with optional eager loading.

        Args:
            session_id: Session ID to retrieve
            load_relations: If True, loads traces and risks in same query (prevents N+1)

        Returns:
            SessionDB instance if found, None otherwise
        """
        query = self.db.query(SessionDB).filter(SessionDB.id == session_id)

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        return query.first()

    def get_by_student(
        self,
        student_id: str,
        load_relations: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionDB]:
        """
        Get all sessions for a student with optional eager loading.

        Args:
            student_id: Student ID
            load_relations: If True, loads traces and risks to prevent N+1 queries
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of SessionDB instances
        """
        query = self.db.query(SessionDB).filter(SessionDB.student_id == student_id)

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        return query.order_by(desc(SessionDB.created_at)).limit(limit).offset(offset).all()

    def get_by_activity(
        self,
        activity_id: str,
        load_relations: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionDB]:
        """
        Get all sessions for an activity with optional eager loading.

        Args:
            activity_id: Activity ID
            load_relations: If True, loads traces and risks to prevent N+1 queries
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of SessionDB instances
        """
        query = self.db.query(SessionDB).filter(SessionDB.activity_id == activity_id)

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        return query.order_by(desc(SessionDB.created_at)).limit(limit).offset(offset).all()

    def get_all(
        self,
        load_relations: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionDB]:
        """
        Get all sessions with optional eager loading.

        Args:
            load_relations: If True, loads traces and risks to prevent N+1 queries
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of SessionDB instances
        """
        query = self.db.query(SessionDB)

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        return query.order_by(desc(SessionDB.created_at)).limit(limit).offset(offset).all()

    def end_session(self, session_id: str) -> Optional[SessionDB]:
        """
        Mark session as completed with pessimistic locking.

        Uses SELECT FOR UPDATE to prevent race conditions.

        Returns:
            SessionDB if session was ended successfully, None otherwise
        """
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.end_time = utc_now()
                session.status = "completed"
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def update_mode(self, session_id: str, mode: str) -> Optional[SessionDB]:
        """Update session mode with pessimistic locking."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.mode = mode
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def update_status(self, session_id: str, status: str) -> Optional[SessionDB]:
        """Update session status with pessimistic locking."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.status = status
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def exists(self, session_id: str) -> bool:
        """Check if session exists without loading full object."""
        return self.db.query(
            exists().where(SessionDB.id == session_id)
        ).scalar()

    def delete(self, session_id: str, validate_cascade: bool = True) -> bool:
        """
        Delete a session (hard delete with CASCADE to related entities).

        WARNING: This will also delete all related traces, risks, evaluations,
        git_traces, interview_sessions, incident_simulations, and lti_sessions.

        Args:
            session_id: Session ID to delete
            validate_cascade: If True, logs cascade impact before deletion

        Returns:
            True if session was deleted, False if session not found
        """
        try:
            session = self.db.query(SessionDB).filter(SessionDB.id == session_id).first()
            if not session:
                return False

            if validate_cascade:
                cascade_counts = {
                    "traces": self.db.query(CognitiveTraceDB).filter(
                        CognitiveTraceDB.session_id == session_id
                    ).count(),
                    "risks": self.db.query(RiskDB).filter(
                        RiskDB.session_id == session_id
                    ).count(),
                    "evaluations": self.db.query(EvaluationDB).filter(
                        EvaluationDB.session_id == session_id
                    ).count(),
                    "git_traces": self.db.query(GitTraceDB).filter(
                        GitTraceDB.session_id == session_id
                    ).count(),
                    "interview_sessions": self.db.query(InterviewSessionDB).filter(
                        InterviewSessionDB.session_id == session_id
                    ).count(),
                    "incident_simulations": self.db.query(IncidentSimulationDB).filter(
                        IncidentSimulationDB.session_id == session_id
                    ).count(),
                }

                total_cascaded = sum(cascade_counts.values())
                if total_cascaded > 0:
                    logger.warning(
                        f"Deleting session {session_id} will CASCADE delete {total_cascaded} related entities",
                        extra={
                            "session_id": session_id,
                            "cascade_counts": cascade_counts,
                            "student_id": session.student_id,
                            "activity_id": session.activity_id,
                        }
                    )

            self.db.delete(session)
            self.db.commit()

            # FIX Cortez53: Use lazy logging
            logger.info("Session %s deleted successfully", session_id)
            return True
        except Exception as e:
            self.db.rollback()
            # FIX Cortez53: Use lazy logging
            logger.error("Failed to delete session %s", session_id, exc_info=True)
            raise

    def get_by_ids(
        self,
        session_ids: List[str],
        load_relations: bool = False
    ) -> Dict[str, SessionDB]:
        """
        Get multiple sessions by IDs in a single query (batch loading).

        Args:
            session_ids: List of session IDs to fetch
            load_relations: If True, eagerly loads traces, risks, evaluations

        Returns:
            Dictionary mapping session_id to SessionDB
        """
        if not session_ids:
            return {}

        query = self.db.query(SessionDB).filter(SessionDB.id.in_(session_ids))

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        sessions = query.all()
        return {session.id: session for session in sessions}

    def count_by_student(self, student_id: str) -> int:
        """Count sessions for a student."""
        return (
            self.db.query(SessionDB)
            .filter(SessionDB.student_id == student_id)
            .count()
        )

    def count_by_activity(self, activity_id: str) -> int:
        """Count sessions for an activity."""
        return (
            self.db.query(SessionDB)
            .filter(SessionDB.activity_id == activity_id)
            .count()
        )

    def get_by_course(
        self,
        course_id: str,
        load_relations: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[SessionDB]:
        """
        Get all sessions for a course with optional eager loading.

        FIX Cortez82: Added for filtering by course/subject.

        Args:
            course_id: Course/subject identifier
            load_relations: If True, loads traces and risks to prevent N+1 queries
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of SessionDB instances
        """
        query = self.db.query(SessionDB).filter(SessionDB.course_id == course_id)

        if load_relations:
            query = query.options(
                selectinload(SessionDB.traces),
                selectinload(SessionDB.risks),
                selectinload(SessionDB.evaluations)
            )

        return query.order_by(desc(SessionDB.created_at)).limit(limit).offset(offset).all()

    def count_by_course(self, course_id: str) -> int:
        """Count sessions for a course. FIX Cortez82."""
        return (
            self.db.query(SessionDB)
            .filter(SessionDB.course_id == course_id)
            .count()
        )

    def update_simulator_type(
        self, session_id: str, simulator_type: str
    ) -> Optional[SessionDB]:
        """Update session simulator_type with pessimistic locking."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.simulator_type = simulator_type
                session.updated_at = utc_now()
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def update_cognitive_status(
        self, session_id: str, cognitive_status: dict
    ) -> Optional[SessionDB]:
        """Update session cognitive status for N4 traceability."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.cognitive_status = cognitive_status
                session.updated_at = utc_now()
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def update_session_metrics(
        self, session_id: str, session_metrics: dict
    ) -> Optional[SessionDB]:
        """Update session metrics (aggregated statistics)."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.session_metrics = session_metrics
                session.updated_at = utc_now()
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise

    def update_learning_objective(
        self, session_id: str, learning_objective: dict
    ) -> Optional[SessionDB]:
        """Update session learning objective."""
        try:
            stmt = select(SessionDB).where(SessionDB.id == session_id).with_for_update()
            session = self.db.execute(stmt).scalar_one_or_none()

            if session:
                session.learning_objective = learning_objective
                session.updated_at = utc_now()
                self.db.commit()
                self.db.refresh(session)
                return session

            return None
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Database operation failed: %s", str(e), exc_info=True)
            raise
