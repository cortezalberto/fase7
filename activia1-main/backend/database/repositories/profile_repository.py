"""
Profile and Misc Repositories - Student profiles, subjects, and trace sequences.

Cortez46: Extracted from repositories.py (5,134 lines)

Contains:
- StudentProfileRepository (Cortez3 Fix 3.1)
- SubjectRepository (FASE 1.5 + FASE 2)
- TraceSequenceRepository
"""
from typing import List, Optional, Dict, Any
from uuid import uuid4
import logging

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from backend.core.constants import utc_now
from ..models import StudentProfileDB, SubjectDB, TraceSequenceDB
from ...models.trace import TraceSequence
from .base import BaseRepository

logger = logging.getLogger(__name__)


class StudentProfileRepository(BaseRepository):
    """
    Repository for student profile operations (Cortez3 Fix 3.1).

    Manages student profiles with analytics and risk metrics.
    FIX Cortez11: Aligned field names with ORM StudentProfileDB
    """

    def create(
        self,
        student_id: str,
        user_id: Optional[str] = None,
        name: Optional[str] = None,
        email: Optional[str] = None,
        preferred_language: str = "es",
        cognitive_preferences: Optional[Dict[str, Any]] = None,
    ) -> StudentProfileDB:
        """
        Create a new student profile.

        Args:
            student_id: Unique student identifier
            user_id: Optional user ID for authenticated students
            name: Student name
            email: Student email
            preferred_language: Preferred language (default: "es")
            cognitive_preferences: Cognitive preferences dict

        Returns:
            Created StudentProfileDB instance
        """
        profile = StudentProfileDB(
            id=str(uuid4()),
            student_id=student_id,
            user_id=user_id,
            name=name,
            email=email,
            preferred_language=preferred_language,
            cognitive_preferences=cognitive_preferences or {},
            total_sessions=0,
            total_interactions=0,
            average_ai_dependency=0.0,
            average_competency_level=None,
            average_competency_score=None,
            total_risks=0,
            critical_risks=0,
            risk_trends={},
            competency_evolution=[],
            last_activity_date=None,
            learning_patterns={},
            competency_levels={},
            strengths=[],
            areas_for_improvement=[],
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        logger.info(
            "Student profile created: %s",
            student_id,
            extra={"student_id": student_id, "profile_id": profile.id}
        )
        return profile

    def get_by_id(self, profile_id: str) -> Optional[StudentProfileDB]:
        """Get profile by internal ID."""
        return self.db.query(StudentProfileDB).filter(
            StudentProfileDB.id == profile_id
        ).first()

    def get_by_student_id(self, student_id: str) -> Optional[StudentProfileDB]:
        """Get profile by student_id (unique identifier)."""
        return self.db.query(StudentProfileDB).filter(
            StudentProfileDB.student_id == student_id
        ).first()

    def get_by_user_id(self, user_id: str) -> Optional[StudentProfileDB]:
        """Get profile by user_id (authenticated user)."""
        return self.db.query(StudentProfileDB).filter(
            StudentProfileDB.user_id == user_id
        ).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[StudentProfileDB]:
        """List all profiles with pagination."""
        return (
            self.db.query(StudentProfileDB)
            .order_by(desc(StudentProfileDB.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def update_analytics(
        self,
        student_id: str,
        total_sessions: int,
        total_interactions: int,
        average_ai_dependency: float,
        total_risks: int = 0,
        critical_risks: int = 0,
        risk_trends: Optional[Dict[str, Any]] = None,
        competency_evolution: Optional[List[Any]] = None,
        average_competency_level: Optional[str] = None,
        average_competency_score: Optional[float] = None,
    ) -> Optional[StudentProfileDB]:
        """Update student analytics metrics."""
        profile = self.get_by_student_id(student_id)
        if not profile:
            return None

        profile.total_sessions = total_sessions
        profile.total_interactions = total_interactions
        profile.average_ai_dependency = average_ai_dependency
        profile.total_risks = total_risks
        profile.critical_risks = critical_risks
        if risk_trends is not None:
            profile.risk_trends = risk_trends
        if competency_evolution is not None:
            profile.competency_evolution = competency_evolution
        if average_competency_level is not None:
            profile.average_competency_level = average_competency_level
        if average_competency_score is not None:
            profile.average_competency_score = average_competency_score
        profile.last_activity_date = utc_now()
        profile.updated_at = utc_now()

        self.db.commit()
        self.db.refresh(profile)

        logger.info(
            "Student analytics updated: %s",
            student_id,
            extra={
                "student_id": student_id,
                "total_sessions": total_sessions,
                "average_ai_dependency": average_ai_dependency
            }
        )
        return profile

    def get_at_risk_students(
        self, ai_dependency_threshold: float = 0.7
    ) -> List[StudentProfileDB]:
        """Get students with high AI dependency risk."""
        return (
            self.db.query(StudentProfileDB)
            .filter(StudentProfileDB.average_ai_dependency >= ai_dependency_threshold)
            .order_by(desc(StudentProfileDB.average_ai_dependency))
            .all()
        )

    def get_by_competency_level(
        self, competency_level: str, limit: int = 100
    ) -> List[StudentProfileDB]:
        """Get students by average competency level."""
        return (
            self.db.query(StudentProfileDB)
            .filter(StudentProfileDB.average_competency_level == competency_level)
            .order_by(desc(StudentProfileDB.created_at))
            .limit(limit)
            .all()
        )

    def update_profile(
        self,
        student_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        preferred_language: Optional[str] = None,
        cognitive_preferences: Optional[Dict[str, Any]] = None,
        learning_patterns: Optional[Dict[str, Any]] = None,
        competency_levels: Optional[Dict[str, str]] = None,
        strengths: Optional[List[str]] = None,
        areas_for_improvement: Optional[List[str]] = None,
    ) -> Optional[StudentProfileDB]:
        """Update student profile information."""
        profile = self.get_by_student_id(student_id)
        if not profile:
            return None

        if name is not None:
            profile.name = name
        if email is not None:
            profile.email = email
        if preferred_language is not None:
            profile.preferred_language = preferred_language
        if cognitive_preferences is not None:
            profile.cognitive_preferences = cognitive_preferences
        if learning_patterns is not None:
            profile.learning_patterns = learning_patterns
        if competency_levels is not None:
            profile.competency_levels = competency_levels
        if strengths is not None:
            profile.strengths = strengths
        if areas_for_improvement is not None:
            profile.areas_for_improvement = areas_for_improvement

        profile.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(profile)

        logger.info("Student profile updated: %s", student_id, extra={"student_id": student_id})
        return profile

    def delete(self, student_id: str) -> bool:
        """Delete student profile."""
        profile = self.get_by_student_id(student_id)
        if not profile:
            return False

        self.db.delete(profile)
        self.db.commit()

        logger.warning("Student profile deleted: %s", student_id, extra={"student_id": student_id})
        return True

    def get_by_ids(self, student_ids: List[str]) -> Dict[str, StudentProfileDB]:
        """
        Get multiple student profiles by IDs in a single query (batch loading).

        FIX 3.5 Cortez5: Batch loading to prevent N+1 queries
        """
        if not student_ids:
            return {}

        profiles = (
            self.db.query(StudentProfileDB)
            .filter(StudentProfileDB.student_id.in_(student_ids))
            .all()
        )
        return {profile.student_id: profile for profile in profiles}


class SubjectRepository(BaseRepository):
    """
    Repository for Subject (materias) operations.

    Manages programming subjects/courses (Python, Java, etc.)
    FASE 1.5 + FASE 2
    """

    def get_all(self, active_only: bool = True) -> List[SubjectDB]:
        """Get all subjects."""
        query = self.db.query(SubjectDB)
        if active_only:
            query = query.filter(SubjectDB.is_active == True)
        return query.order_by(SubjectDB.name).all()

    def get_by_code(self, code: str) -> Optional[SubjectDB]:
        """Get subject by code (e.g., 'PYTHON', 'JAVA')."""
        return self.db.query(SubjectDB).filter(SubjectDB.code == code).first()

    def get_by_language(self, language: str, active_only: bool = True) -> List[SubjectDB]:
        """Get subjects by programming language."""
        query = self.db.query(SubjectDB).filter(SubjectDB.language == language)
        if active_only:
            query = query.filter(SubjectDB.is_active == True)
        return query.all()

    def create(self, subject: SubjectDB) -> SubjectDB:
        """Create new subject."""
        try:
            self.db.add(subject)
            self.db.commit()
            self.db.refresh(subject)
            logger.info("Subject created: %s", subject.code)
            return subject
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error creating subject %s: %s", subject.code, e, exc_info=True)
            raise

    def update(self, code: str, updates: dict) -> Optional[SubjectDB]:
        """Update subject."""
        try:
            subject = self.get_by_code(code)
            if not subject:
                return None

            for key, value in updates.items():
                if hasattr(subject, key):
                    setattr(subject, key, value)

            subject.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(subject)
            logger.info("Subject updated: %s", code)
            return subject
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error updating subject %s: %s", code, e, exc_info=True)
            raise

    def delete(self, code: str) -> bool:
        """Delete subject (hard delete, cascades to exercises)."""
        try:
            subject = self.get_by_code(code)
            if not subject:
                return False

            self.db.delete(subject)
            self.db.commit()
            logger.warning("Subject deleted: %s", code)
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Error deleting subject %s: %s", code, e, exc_info=True)
            raise


class TraceSequenceRepository(BaseRepository):
    """Repository for trace sequence operations."""

    def create(self, sequence: TraceSequence) -> TraceSequenceDB:
        """
        Create a new trace sequence.

        FIX 10.7 Cortez10: Added transaction safety with try/except/rollback.
        """
        try:
            db_sequence = TraceSequenceDB(
                id=sequence.id,
                session_id=sequence.session_id,
                student_id=sequence.student_id,
                activity_id=sequence.activity_id,
                start_time=sequence.start_time,
                end_time=sequence.end_time,
                reasoning_path=sequence.reasoning_path,
                strategy_changes=sequence.strategy_changes,
                ai_dependency_score=sequence.ai_dependency_score,
                trace_ids=[t.id for t in sequence.traces],
            )
            self.db.add(db_sequence)
            self.db.commit()
            self.db.refresh(db_sequence)
            return db_sequence
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create trace sequence: %s", e, exc_info=True)
            raise

    def get_by_id(self, sequence_id: str) -> Optional[TraceSequenceDB]:
        """Get sequence by ID."""
        return (
            self.db.query(TraceSequenceDB)
            .filter(TraceSequenceDB.id == sequence_id)
            .first()
        )

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
        load_relations: bool = False
    ) -> List[TraceSequenceDB]:
        """
        Get all sequences for a session.

        FIX 3.1 Cortez5: Added limit/offset to prevent unbounded queries
        FIX 10.12 Cortez10: Added load_relations option for eager loading
        """
        query = self.db.query(TraceSequenceDB).filter(
            TraceSequenceDB.session_id == session_id
        )

        if load_relations:
            query = query.options(selectinload(TraceSequenceDB.session))

        return (
            query
            .order_by(TraceSequenceDB.start_time)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def count_by_session(self, session_id: str) -> int:
        """Count trace sequences for a session."""
        return (
            self.db.query(TraceSequenceDB)
            .filter(TraceSequenceDB.session_id == session_id)
            .count()
        )

    def count_by_student(self, student_id: str) -> int:
        """Count trace sequences for a student."""
        return (
            self.db.query(TraceSequenceDB)
            .filter(TraceSequenceDB.student_id == student_id)
            .count()
        )
