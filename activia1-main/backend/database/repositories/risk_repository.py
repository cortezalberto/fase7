"""
Risk Repository - Risk database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- RiskRepository: CRUD operations for risks
- Batch loading to prevent N+1 queries
- Orphan trace cleanup utilities
"""
from typing import List, Optional, Dict
from uuid import uuid4
import logging

from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, select

from ..models import RiskDB, SessionDB, CognitiveTraceDB
from ...models.risk import Risk, RiskType, RiskLevel
from backend.core.constants import utc_now
from .base import _safe_enum_to_str

logger = logging.getLogger(__name__)


class RiskRepository:
    """Repository for risk operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(self, risk: Risk) -> RiskDB:
        """
        Create a new risk.

        Args:
            risk: Risk domain model

        Returns:
            Created RiskDB instance
        """
        db_risk = RiskDB(
            id=risk.id or str(uuid4()),
            session_id=risk.session_id,
            student_id=risk.student_id,
            activity_id=risk.activity_id,
            risk_type=_safe_enum_to_str(risk.risk_type, RiskType),
            risk_level=_safe_enum_to_str(risk.risk_level, RiskLevel),
            dimension=risk.dimension.value,
            description=risk.description,
            impact=risk.impact,
            evidence=risk.evidence,
            trace_ids=risk.trace_ids,
            root_cause=risk.root_cause,
            impact_assessment=risk.impact_assessment,
            recommendations=risk.recommendations,
            pedagogical_intervention=risk.pedagogical_intervention,
            resolved=risk.resolved,
            resolution_notes=risk.resolution_notes,
            detected_by=risk.detected_by,
        )
        # FIX Cortez84 HIGH-REPO-001: Use commit instead of flush for persistence
        try:
            self.db.add(db_risk)
            self.db.commit()
            self.db.refresh(db_risk)
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create risk: %s", str(e), exc_info=True)
            raise
        return db_risk

    def get_by_id(self, risk_id: str) -> Optional[RiskDB]:
        """Get risk by ID."""
        return self.db.query(RiskDB).filter(RiskDB.id == risk_id).first()

    def get_by_session(
        self,
        session_id: str,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskDB]:
        """
        Get all risks for a session.

        Args:
            session_id: Session ID to filter by
            resolved: Optional filter by resolution status
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of risks ordered by creation date (newest first)
        """
        query = self.db.query(RiskDB).filter(RiskDB.session_id == session_id)

        # FIX Cortez85 HIGH-ORM-002: Use .is_() for boolean comparisons
        if resolved is not None:
            query = query.filter(RiskDB.resolved.is_(resolved))

        return query.order_by(desc(RiskDB.created_at)).limit(limit).offset(offset).all()

    def get_by_student(
        self,
        student_id: str,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskDB]:
        """
        Get risks for a student with eager loading.

        Args:
            student_id: Student ID to filter by
            resolved: Optional filter by resolution status
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            List of risks with session data preloaded
        """
        query = self.db.query(RiskDB)\
            .filter(RiskDB.student_id == student_id)\
            .options(joinedload(RiskDB.session))

        if resolved is not None:
            query = query.filter(RiskDB.resolved.is_(resolved))

        return query.order_by(desc(RiskDB.created_at)).limit(limit).offset(offset).all()

    def get_critical_risks(
        self,
        student_id: Optional[str] = None,
        load_session_relations: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskDB]:
        """
        Get critical unresolved risks with eager loading and pagination.

        FIX Cortez84 CRIT-REPO-004: Added pagination to prevent memory exhaustion.

        Args:
            student_id: Optional student filter
            load_session_relations: If True, preload traces and evaluations
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of critical risks with relations preloaded
        """
        query = self.db.query(RiskDB)\
            .filter(RiskDB.risk_level == "critical")\
            .filter(RiskDB.resolved.is_(False))

        if student_id:
            query = query.filter(RiskDB.student_id == student_id)

        if load_session_relations:
            query = query.options(
                selectinload(RiskDB.session).selectinload(SessionDB.traces),
                selectinload(RiskDB.session).selectinload(SessionDB.evaluations)
            )
        else:
            query = query.options(joinedload(RiskDB.session))

        return query.order_by(desc(RiskDB.created_at)).limit(limit).offset(offset).all()

    def resolve_risk(self, risk_id: str, resolution_notes: str) -> bool:
        """
        Mark risk as resolved with pessimistic locking.

        Args:
            risk_id: Risk ID to resolve
            resolution_notes: Notes about resolution

        Returns:
            True if resolved, False if not found
        """
        try:
            stmt = select(RiskDB).where(RiskDB.id == risk_id).with_for_update()
            risk = self.db.execute(stmt).scalar_one_or_none()

            if risk:
                risk.resolved = True
                risk.resolved_at = utc_now()
                risk.resolution_notes = resolution_notes
                risk.updated_at = utc_now()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to resolve risk %s: %s", risk_id, e, exc_info=True)
            raise

    def get_by_session_ids(self, session_ids: List[str]) -> Dict[str, List[RiskDB]]:
        """
        Get all risks for multiple sessions in a single query (batch loading).

        Args:
            session_ids: List of session IDs

        Returns:
            Dictionary mapping session_id to list of risks
        """
        if not session_ids:
            return {}

        risks = (
            self.db.query(RiskDB)
            .filter(RiskDB.session_id.in_(session_ids))
            .order_by(RiskDB.session_id, desc(RiskDB.created_at))
            .all()
        )

        result: Dict[str, List[RiskDB]] = {sid: [] for sid in session_ids}
        for risk in risks:
            if risk.session_id in result:
                result[risk.session_id].append(risk)

        return result

    def exists(self, risk_id: str) -> bool:
        """Check if a risk exists without loading the full object."""
        return (
            self.db.query(RiskDB.id)
            .filter(RiskDB.id == risk_id)
            .first() is not None
        )

    def count_by_session(self, session_id: str, include_resolved: bool = True) -> int:
        """
        Count risks for a session.

        Args:
            session_id: Session ID
            include_resolved: If False, only count unresolved risks

        Returns:
            Number of risks
        """
        query = self.db.query(RiskDB).filter(RiskDB.session_id == session_id)
        if not include_resolved:
            query = query.filter(RiskDB.resolved.is_(False))
        return query.count()

    def count_by_level(self, session_id: str, level: str) -> int:
        """
        Count risks of a specific level for a session.

        Args:
            session_id: Session ID
            level: Risk level (low, medium, high, critical)

        Returns:
            Number of risks at specified level
        """
        return (
            self.db.query(RiskDB)
            .filter(
                RiskDB.session_id == session_id,
                RiskDB.risk_level == level.lower()
            )
            .count()
        )

    def clean_orphan_trace_ids(self, risk_id: str) -> int:
        """
        Remove trace_ids that reference deleted traces.

        Args:
            risk_id: Risk ID to clean

        Returns:
            Number of orphan IDs removed
        """
        try:
            # FIX Cortez70 CRIT-DB-003: Use SELECT FOR UPDATE to prevent race conditions
            stmt = select(RiskDB).where(RiskDB.id == risk_id).with_for_update()
            risk = self.db.execute(stmt).scalar_one_or_none()

            if not risk or not risk.trace_ids:
                return 0

            valid_ids = self.db.query(CognitiveTraceDB.id).filter(
                CognitiveTraceDB.id.in_(risk.trace_ids)
            ).all()
            valid_ids_set = {id for (id,) in valid_ids}

            original_count = len(risk.trace_ids)
            risk.trace_ids = [id for id in risk.trace_ids if id in valid_ids_set]
            removed_count = original_count - len(risk.trace_ids)

            if removed_count > 0:
                self.db.commit()
                logger.info(
                    "Cleaned %s orphan trace IDs from risk %s",
                    removed_count, risk_id,
                    extra={"risk_id": risk_id, "removed_count": removed_count}
                )

            return removed_count
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to clean orphan trace IDs for risk %s: %s", risk_id, e, exc_info=True)
            raise

    def clean_all_orphan_trace_ids(self) -> Dict[str, int]:
        """
        Clean orphan trace_ids from all risks.

        Returns:
            Dictionary with total_risks_processed and total_orphans_removed
        """
        try:
            risks_with_traces = self.db.query(RiskDB).filter(
                RiskDB.trace_ids != None,
                RiskDB.trace_ids != []
            ).all()

            total_removed = 0
            risks_processed = 0

            for risk in risks_with_traces:
                removed = self.clean_orphan_trace_ids(risk.id)
                total_removed += removed
                risks_processed += 1

            return {
                "total_risks_processed": risks_processed,
                "total_orphans_removed": total_removed
            }
        except Exception as e:
            logger.error("Failed to clean all orphan trace IDs: %s", e, exc_info=True)
            raise

    def get_by_activity(
        self,
        activity_id: str,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskDB]:
        """
        Get all risks for an activity.

        Args:
            activity_id: Activity ID to filter by
            resolved: Optional filter by resolution status
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            List of risks ordered by creation date (newest first)
        """
        query = self.db.query(RiskDB).filter(RiskDB.activity_id == activity_id)

        if resolved is not None:
            query = query.filter(RiskDB.resolved.is_(resolved))

        return query.order_by(desc(RiskDB.created_at)).limit(limit).offset(offset).all()

    def get_by_dimension(
        self,
        dimension: str,
        resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[RiskDB]:
        """
        Get all risks for a specific dimension.

        Args:
            dimension: Risk dimension (cognitive, ethical, epistemic, technical, governance)
            resolved: Optional filter by resolution status
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            List of risks ordered by creation date (newest first)
        """
        query = self.db.query(RiskDB).filter(RiskDB.dimension == dimension.lower())

        if resolved is not None:
            query = query.filter(RiskDB.resolved.is_(resolved))

        return query.order_by(desc(RiskDB.created_at)).limit(limit).offset(offset).all()
