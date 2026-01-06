"""
Data Aggregators - Reusable data aggregation services.

Cortez89: Architecture improvement - extracted from God Classes.

Provides:
- CohortDataAggregator: Aggregates student data for reporting
- RiskDataAggregator: Aggregates risk metrics

Benefits:
- Single Responsibility: Each aggregator has one job
- Reusable: Used by CourseReportGenerator and InstitutionalRiskManager
- Testable: Small, focused classes are easy to test
- ~300 lines extracted from CourseReportGenerator
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..database.models import (
    SessionDB,
    CognitiveTraceDB,
    RiskDB,
    EvaluationDB,
)

logger = logging.getLogger(__name__)


class CohortDataAggregator:
    """
    Cortez89: Aggregates cohort-level statistics from database.

    Extracted from CourseReportGenerator to enable reuse and testing.

    Handles:
    - Summary statistics (sessions, interactions, AI dependency)
    - Competency distribution
    - Student-level summaries with batch queries
    - At-risk student identification

    All methods use batch queries to prevent N+1 performance issues.
    """

    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session

    def aggregate_summary_stats(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Aggregate summary statistics for a cohort.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary with:
            - total_students: Number of students
            - total_sessions: Total sessions in period
            - total_interactions: Total cognitive traces
            - avg_sessions_per_student: Average sessions per student
            - avg_interactions_per_student: Average interactions per student
            - avg_ai_dependency: Average AI involvement (0.0-1.0)
            - total_risks: Total risks detected
        """
        if not student_ids:
            return self._empty_summary_stats()

        # Total sessions
        total_sessions = (
            self.db.query(SessionDB)
            .filter(
                SessionDB.student_id.in_(student_ids),
                SessionDB.start_time >= period_start,
                SessionDB.start_time <= period_end,
            )
            .count()
        )

        # Total interactions (cognitive traces)
        total_interactions = (
            self.db.query(CognitiveTraceDB)
            .filter(
                CognitiveTraceDB.student_id.in_(student_ids),
                CognitiveTraceDB.created_at >= period_start,
                CognitiveTraceDB.created_at <= period_end,
            )
            .count()
        )

        # Average AI dependency
        avg_ai_dependency = (
            self.db.query(func.avg(CognitiveTraceDB.ai_involvement))
            .filter(
                CognitiveTraceDB.student_id.in_(student_ids),
                CognitiveTraceDB.created_at >= period_start,
                CognitiveTraceDB.created_at <= period_end,
            )
            .scalar()
            or 0.0
        )

        # Total risks
        total_risks = (
            self.db.query(RiskDB)
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .count()
        )

        student_count = len(student_ids)
        return {
            "total_students": student_count,
            "total_sessions": total_sessions,
            "total_interactions": total_interactions,
            "avg_sessions_per_student": round(total_sessions / student_count, 2),
            "avg_interactions_per_student": round(total_interactions / student_count, 2),
            "avg_ai_dependency": round(float(avg_ai_dependency), 3),
            "total_risks": total_risks,
        }

    def _empty_summary_stats(self) -> Dict[str, Any]:
        """Return empty summary stats structure."""
        return {
            "total_students": 0,
            "total_sessions": 0,
            "total_interactions": 0,
            "avg_sessions_per_student": 0,
            "avg_interactions_per_student": 0,
            "avg_ai_dependency": 0.0,
            "total_risks": 0,
        }

    def aggregate_competency_distribution(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """
        Get distribution of competency levels across evaluations.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary mapping competency level to count
            (BASICO, INTERMEDIO, AVANZADO, EXPERTO)
        """
        evaluations = (
            self.db.query(
                EvaluationDB.overall_competency_level,
                func.count(EvaluationDB.id).label("count"),
            )
            .filter(
                EvaluationDB.student_id.in_(student_ids),
                EvaluationDB.created_at >= period_start,
                EvaluationDB.created_at <= period_end,
            )
            .group_by(EvaluationDB.overall_competency_level)
            .all()
        )

        distribution = {level: count for level, count in evaluations}

        # Ensure all levels are present
        for level in ["BASICO", "INTERMEDIO", "AVANZADO", "EXPERTO"]:
            if level not in distribution:
                distribution[level] = 0

        return distribution

    def generate_student_summaries(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """
        Generate individual student summaries using batch queries.

        Uses 5 batch queries instead of N*5 individual queries.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            List of dictionaries with student metrics
        """
        if not student_ids:
            return []

        # Batch query 1: Sessions count per student
        sessions_by_student = self._batch_count_sessions(
            student_ids, period_start, period_end
        )

        # Batch query 2: AI dependency per student
        ai_dependency_by_student = self._batch_avg_ai_dependency(
            student_ids, period_start, period_end
        )

        # Batch query 3: Latest competency per student
        competency_by_student = self._batch_latest_competency(
            student_ids, period_start, period_end
        )

        # Batch query 4: Total risks per student
        risks_by_student = self._batch_count_risks(
            student_ids, period_start, period_end
        )

        # Batch query 5: Critical risks per student
        critical_risks_by_student = self._batch_count_critical_risks(
            student_ids, period_start, period_end
        )

        # Build summaries from batch results (no additional queries)
        summaries = []
        for student_id in student_ids:
            summaries.append({
                "student_id": student_id,
                "sessions": sessions_by_student.get(student_id, 0),
                "ai_dependency": round(ai_dependency_by_student.get(student_id, 0.0), 3),
                "competency": competency_by_student.get(student_id, "N/A"),
                "risks": risks_by_student.get(student_id, 0),
                "critical_risks": critical_risks_by_student.get(student_id, 0),
            })

        return summaries

    def _batch_count_sessions(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """Batch query for session counts per student."""
        results = (
            self.db.query(
                SessionDB.student_id,
                func.count(SessionDB.id).label("count")
            )
            .filter(
                SessionDB.student_id.in_(student_ids),
                SessionDB.start_time >= period_start,
                SessionDB.start_time <= period_end,
            )
            .group_by(SessionDB.student_id)
            .all()
        )
        return {r.student_id: r.count for r in results}

    def _batch_avg_ai_dependency(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, float]:
        """Batch query for average AI dependency per student."""
        results = (
            self.db.query(
                CognitiveTraceDB.student_id,
                func.avg(CognitiveTraceDB.ai_involvement).label("avg_ai")
            )
            .filter(
                CognitiveTraceDB.student_id.in_(student_ids),
                CognitiveTraceDB.created_at >= period_start,
                CognitiveTraceDB.created_at <= period_end,
            )
            .group_by(CognitiveTraceDB.student_id)
            .all()
        )
        return {r.student_id: float(r.avg_ai or 0.0) for r in results}

    def _batch_latest_competency(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, str]:
        """Batch query for latest competency level per student."""
        # Subquery to get latest evaluation date per student
        latest_evals_subquery = (
            self.db.query(
                EvaluationDB.student_id,
                func.max(EvaluationDB.created_at).label("max_created")
            )
            .filter(
                EvaluationDB.student_id.in_(student_ids),
                EvaluationDB.created_at >= period_start,
                EvaluationDB.created_at <= period_end,
            )
            .group_by(EvaluationDB.student_id)
            .subquery()
        )

        # Join to get actual evaluations
        results = (
            self.db.query(EvaluationDB)
            .join(
                latest_evals_subquery,
                and_(
                    EvaluationDB.student_id == latest_evals_subquery.c.student_id,
                    EvaluationDB.created_at == latest_evals_subquery.c.max_created
                )
            )
            .all()
        )
        return {e.student_id: e.overall_competency_level for e in results}

    def _batch_count_risks(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """Batch query for total risk count per student."""
        results = (
            self.db.query(
                RiskDB.student_id,
                func.count(RiskDB.id).label("count")
            )
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.student_id)
            .all()
        )
        return {r.student_id: r.count for r in results}

    def _batch_count_critical_risks(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """Batch query for critical risk count per student."""
        results = (
            self.db.query(
                RiskDB.student_id,
                func.count(RiskDB.id).label("count")
            )
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.risk_level == "critical",
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.student_id)
            .all()
        )
        return {r.student_id: r.count for r in results}

    def identify_at_risk_students(
        self,
        student_summaries: List[Dict[str, Any]],
        ai_dependency_threshold: float = 0.7,
        min_sessions_threshold: int = 3
    ) -> List[str]:
        """
        Identify students requiring intervention.

        Criteria:
        - Critical risks > 0
        - AI dependency > threshold
        - Low sessions (< threshold)
        - Competency is BASICO or N/A

        Args:
            student_summaries: List from generate_student_summaries()
            ai_dependency_threshold: AI dependency cutoff (default 0.7)
            min_sessions_threshold: Minimum expected sessions (default 3)

        Returns:
            List of at-risk student IDs
        """
        at_risk = []

        for summary in student_summaries:
            if (
                summary["critical_risks"] > 0
                or summary["ai_dependency"] > ai_dependency_threshold
                or (0 < summary["sessions"] < min_sessions_threshold)
                or summary["competency"] in ["BASICO", "N/A"]
            ):
                at_risk.append(summary["student_id"])

        return at_risk


class RiskDataAggregator:
    """
    Cortez89: Aggregates risk-related statistics from database.

    Extracted from CourseReportGenerator and InstitutionalRiskManager
    to enable reuse and testing.

    Handles:
    - Risk distribution by level
    - Risk distribution by dimension
    - Top risk types
    - Student categorization by risk
    - Risk trend analysis
    """

    def __init__(self, db_session: Session):
        """Initialize with database session."""
        self.db = db_session

    def aggregate_risk_distribution(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """
        Get distribution of risk levels.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary mapping risk level to count
            (low, medium, high, critical)
        """
        risks = (
            self.db.query(RiskDB.risk_level, func.count(RiskDB.id).label("count"))
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.risk_level)
            .all()
        )

        distribution = {level: count for level, count in risks}

        # Ensure all levels are present (DB stores lowercase)
        for level in ["low", "medium", "high", "critical"]:
            if level not in distribution:
                distribution[level] = 0

        return distribution

    def aggregate_risk_by_dimension(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, int]:
        """
        Get distribution of risks by dimension.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary mapping dimension to count
        """
        risks = (
            self.db.query(RiskDB.dimension, func.count(RiskDB.id).label("count"))
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.dimension)
            .all()
        )

        return {dimension: count for dimension, count in risks}

    def get_top_risks(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get top N most frequent risk types.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period
            limit: Maximum number of risk types to return

        Returns:
            List of dictionaries with risk_type, dimension, count
        """
        risks = (
            self.db.query(
                RiskDB.risk_type,
                RiskDB.dimension,
                func.count(RiskDB.id).label("count"),
            )
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.risk_type, RiskDB.dimension)
            .order_by(func.count(RiskDB.id).desc())
            .limit(limit)
            .all()
        )

        return [
            {"risk_type": risk_type, "dimension": dimension, "count": count}
            for risk_type, dimension, count in risks
        ]

    def categorize_students_by_risk(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, List[str]]:
        """
        Categorize students by their highest risk level.

        Uses a single batch query with MAX CASE.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary mapping risk level to list of student IDs
        """
        categorized: Dict[str, List[str]] = {
            "critical": [], "high": [], "medium": [], "low": [], "none": []
        }

        if not student_ids:
            return categorized

        # Batch query: Get highest risk level per student using MAX CASE
        highest_risk_query = (
            self.db.query(
                RiskDB.student_id,
                func.max(
                    func.case(
                        (RiskDB.risk_level == "critical", 4),
                        (RiskDB.risk_level == "high", 3),
                        (RiskDB.risk_level == "medium", 2),
                        (RiskDB.risk_level == "low", 1),
                        else_=0,
                    )
                ).label("severity")
            )
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .group_by(RiskDB.student_id)
            .all()
        )

        # Map severity score back to risk level
        severity_to_level = {4: "critical", 3: "high", 2: "medium", 1: "low", 0: "none"}
        highest_risk_by_student = {
            r.student_id: severity_to_level.get(r.severity, "none")
            for r in highest_risk_query
        }

        # Categorize all students
        for student_id in student_ids:
            risk_level = highest_risk_by_student.get(student_id, "none")
            categorized[risk_level].append(student_id)

        return categorized

    def analyze_risk_trends(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Analyze risk trends over time.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Dictionary with weekly_counts and trend
            (increasing, stable, decreasing, insufficient_data)
        """
        risks = (
            self.db.query(RiskDB)
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .all()
        )

        # Group by week
        weekly_counts: Dict[str, int] = {}
        for risk in risks:
            week_key = risk.created_at.strftime("%Y-W%W")
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1

        # Calculate trend
        trend = self._calculate_trend(weekly_counts)

        return {"weekly_counts": weekly_counts, "trend": trend}

    def _calculate_trend(self, weekly_counts: Dict[str, int]) -> str:
        """Calculate trend direction from weekly counts."""
        if len(weekly_counts) < 2:
            return "insufficient_data"

        weeks = sorted(weekly_counts.keys())
        first_half = sum(weekly_counts[w] for w in weeks[:len(weeks) // 2])
        second_half = sum(weekly_counts[w] for w in weeks[len(weeks) // 2:])

        if second_half > first_half * 1.2:
            return "increasing"
        elif second_half < first_half * 0.8:
            return "decreasing"
        else:
            return "stable"

    def count_students_with_risks(
        self,
        student_ids: List[str],
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """
        Count unique students who have at least one risk.

        Args:
            student_ids: List of student UUIDs
            period_start: Start of reporting period
            period_end: End of reporting period

        Returns:
            Number of unique students with risks
        """
        result = (
            self.db.query(func.count(func.distinct(RiskDB.student_id)))
            .filter(
                RiskDB.student_id.in_(student_ids),
                RiskDB.created_at >= period_start,
                RiskDB.created_at <= period_end,
            )
            .scalar()
        )
        return result or 0


__all__ = [
    "CohortDataAggregator",
    "RiskDataAggregator",
]
