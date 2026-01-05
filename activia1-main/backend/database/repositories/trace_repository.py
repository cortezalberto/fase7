"""
Trace Repository - Cognitive trace database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- TraceRepository: CRUD operations for cognitive traces
- Batch loading to prevent N+1 queries
- Filtered queries with pagination
"""
from typing import List, Optional, Dict, Tuple
from uuid import uuid4
import logging

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_, and_

from ..models import CognitiveTraceDB
from ...models.trace import CognitiveTrace, TraceLevel, InteractionType
from .base import _safe_enum_to_str, _safe_cognitive_state_to_str

logger = logging.getLogger(__name__)


class TraceRepository:
    """Repository for cognitive trace operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(self, trace: CognitiveTrace) -> CognitiveTraceDB:
        """
        Create a new cognitive trace.

        Args:
            trace: CognitiveTrace domain model

        Returns:
            Created CognitiveTraceDB instance
        """
        db_trace = CognitiveTraceDB(
            id=trace.id or str(uuid4()),
            session_id=trace.session_id,
            student_id=trace.student_id,
            activity_id=trace.activity_id,
            trace_level=_safe_enum_to_str(trace.trace_level, TraceLevel),
            interaction_type=_safe_enum_to_str(trace.interaction_type, InteractionType),
            content=trace.content,
            context=trace.context,
            trace_metadata=trace.trace_metadata,
            cognitive_state=_safe_cognitive_state_to_str(trace.cognitive_state),
            cognitive_intent=trace.cognitive_intent,
            decision_justification=trace.decision_justification,
            alternatives_considered=trace.alternatives_considered,
            strategy_type=trace.strategy_type,
            ai_involvement=trace.ai_involvement,
            parent_trace_id=trace.parent_trace_id,
            agent_id=trace.agent_id,
        )
        # FIX Cortez84 HIGH-REPO-001: Use commit instead of flush for persistence
        try:
            self.db.add(db_trace)
            self.db.commit()
            self.db.refresh(db_trace)
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create trace: %s", str(e), exc_info=True)
            raise
        return db_trace

    def get_by_id(self, trace_id: str) -> Optional[CognitiveTraceDB]:
        """Get trace by ID."""
        return self.db.query(CognitiveTraceDB).filter(CognitiveTraceDB.id == trace_id).first()

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[CognitiveTraceDB]:
        """
        Get all traces for a session.

        Args:
            session_id: Session ID
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of traces ordered by creation date
        """
        return (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.session_id == session_id)
            .order_by(CognitiveTraceDB.created_at)
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_latest_by_session(self, session_id: str) -> Optional[CognitiveTraceDB]:
        """Get only the latest trace for a session."""
        return (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.session_id == session_id)
            .order_by(desc(CognitiveTraceDB.created_at))
            .first()
        )

    def get_by_session_filtered(
        self,
        session_id: str,
        trace_level: Optional[str] = None,
        interaction_type: Optional[str] = None,
        cognitive_state: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CognitiveTraceDB]:
        """
        Get traces with filtering in SQL instead of Python.

        Args:
            session_id: Session ID
            trace_level: Optional trace level filter
            interaction_type: Optional interaction type filter
            cognitive_state: Optional cognitive state filter
            limit: Maximum records to return
            offset: Records to skip

        Returns:
            Filtered list of traces
        """
        query = self.db.query(CognitiveTraceDB).filter(
            CognitiveTraceDB.session_id == session_id
        )

        if trace_level:
            query = query.filter(CognitiveTraceDB.trace_level == trace_level)
        if interaction_type:
            query = query.filter(CognitiveTraceDB.interaction_type == interaction_type)
        if cognitive_state:
            query = query.filter(CognitiveTraceDB.cognitive_state == cognitive_state)

        return (
            query
            .order_by(CognitiveTraceDB.created_at)
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_session_filtered(
        self,
        session_id: str,
        trace_level: Optional[str] = None,
        interaction_type: Optional[str] = None,
        cognitive_state: Optional[str] = None
    ) -> int:
        """Count traces with filtering in SQL for pagination metadata."""
        query = self.db.query(CognitiveTraceDB).filter(
            CognitiveTraceDB.session_id == session_id
        )

        if trace_level:
            query = query.filter(CognitiveTraceDB.trace_level == trace_level)
        if interaction_type:
            query = query.filter(CognitiveTraceDB.interaction_type == interaction_type)
        if cognitive_state:
            query = query.filter(CognitiveTraceDB.cognitive_state == cognitive_state)

        return query.count()

    def get_by_student(self, student_id: str, limit: int = 100) -> List[CognitiveTraceDB]:
        """Get recent traces for a student with eager loading."""
        return (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.student_id == student_id)
            .options(joinedload(CognitiveTraceDB.session))
            .order_by(desc(CognitiveTraceDB.created_at))
            .limit(limit)
            .all()
        )

    def get_by_student_filtered(
        self,
        student_id: str,
        activity_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CognitiveTraceDB]:
        """Get student traces with SQL filtering."""
        query = self.db.query(CognitiveTraceDB).filter(
            CognitiveTraceDB.student_id == student_id
        )

        if activity_id:
            query = query.filter(CognitiveTraceDB.activity_id == activity_id)

        return (
            query
            .order_by(desc(CognitiveTraceDB.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def count_by_student_filtered(
        self,
        student_id: str,
        activity_id: Optional[str] = None
    ) -> int:
        """Count student traces with SQL filtering."""
        query = self.db.query(CognitiveTraceDB).filter(
            CognitiveTraceDB.student_id == student_id
        )

        if activity_id:
            query = query.filter(CognitiveTraceDB.activity_id == activity_id)

        return query.count()

    def count_by_session(self, session_id: str) -> int:
        """Count traces in a session."""
        return (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.session_id == session_id)
            .count()
        )

    def get_by_session_ids(self, session_ids: List[str]) -> Dict[str, List[CognitiveTraceDB]]:
        """
        Get all traces for multiple sessions in a single query (batch loading).

        Args:
            session_ids: List of session IDs to fetch traces for

        Returns:
            Dictionary mapping session_id to list of traces
        """
        if not session_ids:
            return {}

        traces = (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.session_id.in_(session_ids))
            .order_by(CognitiveTraceDB.session_id, CognitiveTraceDB.created_at)
            .all()
        )

        result: Dict[str, List[CognitiveTraceDB]] = {sid: [] for sid in session_ids}
        for trace in traces:
            if trace.session_id in result:
                result[trace.session_id].append(trace)

        return result

    def get_by_student_activity_pairs(
        self,
        pairs: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], List[CognitiveTraceDB]]:
        """
        Batch loading for student-activity pairs.

        Args:
            pairs: List of tuples (student_id, activity_id)

        Returns:
            Dictionary mapping each pair to its traces
        """
        if not pairs:
            return {}

        filters = [
            and_(
                CognitiveTraceDB.student_id == student_id,
                CognitiveTraceDB.activity_id == activity_id
            )
            for student_id, activity_id in pairs
        ]

        traces = (
            self.db.query(CognitiveTraceDB)
            .filter(or_(*filters))
            .order_by(
                CognitiveTraceDB.student_id,
                CognitiveTraceDB.activity_id,
                CognitiveTraceDB.created_at
            )
            .all()
        )

        result: Dict[Tuple[str, str], List[CognitiveTraceDB]] = {
            pair: [] for pair in pairs
        }

        for trace in traces:
            key = (trace.student_id, trace.activity_id)
            if key in result:
                result[key].append(trace)

        return result

    def get_by_activity(
        self,
        activity_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[CognitiveTraceDB]:
        """Get all traces for an activity."""
        return (
            self.db.query(CognitiveTraceDB)
            .filter(CognitiveTraceDB.activity_id == activity_id)
            .order_by(desc(CognitiveTraceDB.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
