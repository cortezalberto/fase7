"""
Evaluation Repository - Evaluation database operations.

Cortez42: Extracted from monolithic repositories.py (5,134 lines)

Provides:
- EvaluationRepository: CRUD operations for evaluations
- Batch loading to prevent N+1 queries
- Session-based evaluation queries
"""
from typing import List, Optional, Dict
from uuid import uuid4
import logging

from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from ..models import EvaluationDB
from ...models.evaluation import EvaluationReport, CompetencyLevel
from .base import _safe_enum_to_str

logger = logging.getLogger(__name__)


class EvaluationRepository:
    """Repository for evaluation operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def create(self, evaluation: EvaluationReport) -> EvaluationDB:
        """
        Create a new evaluation.

        Note: EvaluationReport Pydantic model has separate fields
        (recommendations_student, recommendations_teacher), but the database
        stores them combined in a single 'recommendations' JSON field.

        Args:
            evaluation: EvaluationReport domain model

        Returns:
            Created EvaluationDB instance
        """
        # Combine student and teacher recommendations
        recommendations = {
            "student": evaluation.recommendations_student,
            "teacher": evaluation.recommendations_teacher,
        }

        # Handle reasoning_analysis (Optional field)
        reasoning_analysis_dict = {}
        if evaluation.reasoning_analysis is not None:
            reasoning_analysis_dict = evaluation.reasoning_analysis.model_dump()

        # Handle git_analysis (Optional field)
        git_analysis_dict = {}
        if evaluation.git_analysis is not None:
            git_analysis_dict = evaluation.git_analysis.model_dump()

        # Map ai_dependency_score + ai_usage_patterns to ai_dependency_metrics JSON
        ai_dependency_metrics = {
            "score": evaluation.ai_dependency_score,
            "usage_patterns": evaluation.ai_usage_patterns,
            "reasoning_map": evaluation.reasoning_map,
        }

        db_evaluation = EvaluationDB(
            id=str(uuid4()),
            session_id=evaluation.session_id,
            student_id=evaluation.student_id,
            activity_id=evaluation.activity_id,
            overall_competency_level=_safe_enum_to_str(evaluation.overall_competency_level, CompetencyLevel),
            overall_score=evaluation.overall_score,
            dimensions=[d.model_dump() for d in evaluation.dimensions],
            key_strengths=evaluation.key_strengths,
            improvement_areas=evaluation.improvement_areas,
            recommendations=recommendations,
            reasoning_analysis=reasoning_analysis_dict,
            git_analysis=git_analysis_dict,
            ai_dependency_metrics=ai_dependency_metrics,
        )
        # FIX Cortez85 HIGH-REPO-001: Add try/except for proper error handling
        try:
            self.db.add(db_evaluation)
            self.db.commit()
            self.db.refresh(db_evaluation)
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create evaluation: %s", str(e), exc_info=True)
            raise
        return db_evaluation

    def get_by_id(self, evaluation_id: str) -> Optional[EvaluationDB]:
        """Get evaluation by ID."""
        return self.db.query(EvaluationDB).filter(EvaluationDB.id == evaluation_id).first()

    def get_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationDB]:
        """
        Get all evaluations for a session.

        Args:
            session_id: Session ID to filter by
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of evaluations ordered by creation date (newest first)
        """
        return (
            self.db.query(EvaluationDB)
            .filter(EvaluationDB.session_id == session_id)
            .order_by(desc(EvaluationDB.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_by_student(
        self,
        student_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationDB]:
        """
        Get evaluations for a student with pagination.

        Args:
            student_id: Student ID
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of evaluations for the student
        """
        return (
            self.db.query(EvaluationDB)
            .filter(EvaluationDB.student_id == student_id)
            .order_by(desc(EvaluationDB.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_latest_by_session_ids(self, session_ids: List[str]) -> Dict[str, EvaluationDB]:
        """
        Get latest evaluation per session in single query (batch loading).

        Args:
            session_ids: List of session IDs

        Returns:
            Dictionary mapping session_id to the latest evaluation
        """
        if not session_ids:
            return {}

        # Subquery to get max created_at per session
        subq = self.db.query(
            EvaluationDB.session_id,
            func.max(EvaluationDB.created_at).label('max_created')
        ).filter(
            EvaluationDB.session_id.in_(session_ids)
        ).group_by(EvaluationDB.session_id).subquery()

        # Join to get full evaluation records
        evals = self.db.query(EvaluationDB).join(
            subq,
            and_(
                EvaluationDB.session_id == subq.c.session_id,
                EvaluationDB.created_at == subq.c.max_created
            )
        ).all()

        return {e.session_id: e for e in evals}

    def get_by_session_ids(self, session_ids: List[str]) -> Dict[str, List[EvaluationDB]]:
        """
        Get all evaluations for multiple sessions in single query (batch loading).

        Args:
            session_ids: List of session IDs

        Returns:
            Dictionary mapping session_id to list of evaluations
        """
        if not session_ids:
            return {}

        evals = (
            self.db.query(EvaluationDB)
            .filter(EvaluationDB.session_id.in_(session_ids))
            .order_by(EvaluationDB.session_id, desc(EvaluationDB.created_at))
            .all()
        )

        result: Dict[str, List[EvaluationDB]] = {sid: [] for sid in session_ids}
        for eval in evals:
            if eval.session_id in result:
                result[eval.session_id].append(eval)

        return result

    def get_by_activity(
        self,
        activity_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[EvaluationDB]:
        """
        Get all evaluations for an activity.

        Args:
            activity_id: Activity ID to filter by
            limit: Maximum records to return (default 100)
            offset: Records to skip (default 0)

        Returns:
            List of evaluations ordered by creation date (newest first)
        """
        return (
            self.db.query(EvaluationDB)
            .filter(EvaluationDB.activity_id == activity_id)
            .order_by(desc(EvaluationDB.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
