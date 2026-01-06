"""
Recommendation Engine - Generates institutional recommendations.

Cortez89: Architecture improvement - extracted from God Classes.

Provides:
- InstitutionalRecommendationEngine: Generates recommendations based on cohort data

Benefits:
- Single Responsibility: Focused on recommendation logic only
- Reusable: Used by CourseReportGenerator and InstitutionalRiskManager
- Configurable: Thresholds can be adjusted
- Testable: Pure logic, no database dependencies
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class InstitutionalRecommendationEngine:
    """
    Cortez89: Generates institutional recommendations based on cohort metrics.

    Extracted from CourseReportGenerator to enable reuse and testing.

    Analyzes:
    - AI dependency levels
    - Student engagement (sessions)
    - Risk distribution
    - Competency levels

    Generates:
    - Prioritized recommendations
    - Urgency indicators
    - Suggested interventions
    """

    # Default thresholds (can be overridden in constructor)
    DEFAULT_THRESHOLDS = {
        "ai_dependency_warning": 0.6,  # Warn if avg AI dependency > this
        "ai_dependency_critical": 0.8,  # Critical if avg AI dependency > this
        "min_sessions_per_student": 3,  # Warn if avg sessions < this
        "basic_competency_ratio": 0.4,  # Warn if >40% at BASICO level
        "critical_risk_threshold": 0,  # Alert if any critical risks
    }

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize recommendation engine.

        Args:
            thresholds: Custom threshold values (optional)
        """
        self.thresholds = {**self.DEFAULT_THRESHOLDS, **(thresholds or {})}

    def generate_recommendations(
        self,
        summary_stats: Dict[str, Any],
        competency_distribution: Dict[str, int],
        risk_distribution: Dict[str, int],
        top_risks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate institutional recommendations based on cohort data.

        Args:
            summary_stats: Cohort summary statistics
            competency_distribution: Distribution of competency levels
            risk_distribution: Distribution of risk levels
            top_risks: List of most frequent risks

        Returns:
            List of recommendation strings, ordered by priority
        """
        recommendations = []

        # Check AI dependency
        ai_rec = self._check_ai_dependency(summary_stats)
        if ai_rec:
            recommendations.append(ai_rec)

        # Check engagement
        engagement_rec = self._check_engagement(summary_stats)
        if engagement_rec:
            recommendations.append(engagement_rec)

        # Check critical risks
        risk_rec = self._check_critical_risks(risk_distribution)
        if risk_rec:
            recommendations.append(risk_rec)

        # Check competency distribution
        competency_rec = self._check_competency_distribution(competency_distribution)
        if competency_rec:
            recommendations.append(competency_rec)

        # Check top risk patterns
        pattern_rec = self._check_risk_patterns(top_risks)
        if pattern_rec:
            recommendations.append(pattern_rec)

        # Default positive message if no issues
        if not recommendations:
            recommendations.append(
                "Cohorte en buen estado general. Continuar monitoreo regular."
            )

        return recommendations

    def _check_ai_dependency(self, summary_stats: Dict[str, Any]) -> Optional[str]:
        """Check AI dependency levels."""
        avg_ai = summary_stats.get("avg_ai_dependency", 0)

        if avg_ai > self.thresholds["ai_dependency_critical"]:
            return (
                f"CRITICO: Dependencia promedio de IA muy alta ({avg_ai:.1%}). "
                "Implementar sesiones de trabajo autónomo obligatorias y "
                "limitar temporalmente el acceso a funciones de asistencia IA."
            )
        elif avg_ai > self.thresholds["ai_dependency_warning"]:
            return (
                f"ALERTA: Dependencia promedio de IA alta ({avg_ai:.1%}). "
                "Considerar talleres sobre uso crítico de IA y autonomía cognitiva."
            )
        return None

    def _check_engagement(self, summary_stats: Dict[str, Any]) -> Optional[str]:
        """Check student engagement levels."""
        avg_sessions = summary_stats.get("avg_sessions_per_student", 0)

        if avg_sessions < self.thresholds["min_sessions_per_student"]:
            return (
                f"Bajo engagement: promedio {avg_sessions:.1f} sesiones por estudiante. "
                "Considerar mejorar comunicación sobre disponibilidad del sistema."
            )
        return None

    def _check_critical_risks(self, risk_distribution: Dict[str, int]) -> Optional[str]:
        """Check for critical risks."""
        critical_count = risk_distribution.get("critical", 0)

        if critical_count > self.thresholds["critical_risk_threshold"]:
            return (
                f"URGENTE: {critical_count} riesgos críticos detectados. "
                "Requiere intervención docente inmediata."
            )

        high_count = risk_distribution.get("high", 0)
        if high_count > 5:
            return (
                f"ATENCION: {high_count} riesgos de nivel alto detectados. "
                "Programar seguimiento individual con estudiantes afectados."
            )
        return None

    def _check_competency_distribution(
        self,
        competency_distribution: Dict[str, int]
    ) -> Optional[str]:
        """Check competency level distribution."""
        basic_count = competency_distribution.get("BASICO", 0)
        total_evaluated = sum(competency_distribution.values())

        if total_evaluated > 0:
            basic_ratio = basic_count / total_evaluated
            if basic_ratio > self.thresholds["basic_competency_ratio"]:
                return (
                    f"Alta proporción de competencia BASICA ({basic_ratio:.0%}). "
                    "Considerar reforzar contenidos fundamentales o ajustar evaluación."
                )
        return None

    def _check_risk_patterns(
        self,
        top_risks: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Check for dominant risk patterns."""
        if not top_risks:
            return None

        top_risk = top_risks[0]
        risk_type = top_risk.get("risk_type", "desconocido")
        count = top_risk.get("count", 0)

        if count >= 5:
            return (
                f"Riesgo más frecuente: {risk_type} ({count} casos). "
                "Considerar intervención pedagógica focalizada."
            )
        return None

    def prioritize_recommendations(
        self,
        recommendations: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Convert recommendations to prioritized format with metadata.

        Args:
            recommendations: List of recommendation strings

        Returns:
            List of dictionaries with text, priority, and category
        """
        prioritized = []

        for rec in recommendations:
            if rec.startswith("CRITICO:"):
                priority = "critical"
                category = "immediate_action"
            elif rec.startswith("URGENTE:"):
                priority = "high"
                category = "immediate_action"
            elif rec.startswith("ALERTA:") or rec.startswith("ATENCION:"):
                priority = "medium"
                category = "monitor"
            else:
                priority = "low"
                category = "informational"

            prioritized.append({
                "text": rec,
                "priority": priority,
                "category": category,
            })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        prioritized.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return prioritized


class AlertGenerator:
    """
    Cortez89: Generates alerts based on risk patterns.

    Extracted from InstitutionalRiskManager.

    Handles:
    - Threshold-based alert generation
    - Alert severity determination
    - Evidence collection
    """

    # Alert thresholds
    DEFAULT_ALERT_THRESHOLDS = {
        "critical_risk_count": 1,  # Alert on any critical risk
        "high_risk_count": 3,  # Alert if >3 high risks
        "ai_dependency": 0.8,  # Alert if AI dependency > 80%
        "consecutive_delegation": 3,  # Alert on 3+ consecutive delegations
    }

    def __init__(self, thresholds: Optional[Dict[str, Any]] = None):
        """Initialize alert generator."""
        self.thresholds = {**self.DEFAULT_ALERT_THRESHOLDS, **(thresholds or {})}

    def should_generate_alert(
        self,
        student_metrics: Dict[str, Any]
    ) -> bool:
        """
        Determine if student metrics warrant an alert.

        Args:
            student_metrics: Dictionary with student risk/engagement data

        Returns:
            True if alert should be generated
        """
        critical_risks = student_metrics.get("critical_risks", 0)
        if critical_risks >= self.thresholds["critical_risk_count"]:
            return True

        ai_dependency = student_metrics.get("ai_dependency", 0)
        if ai_dependency >= self.thresholds["ai_dependency"]:
            return True

        high_risks = student_metrics.get("high_risks", 0)
        if high_risks >= self.thresholds["high_risk_count"]:
            return True

        return False

    def determine_severity(
        self,
        student_metrics: Dict[str, Any]
    ) -> str:
        """
        Determine alert severity based on metrics.

        Args:
            student_metrics: Dictionary with student risk/engagement data

        Returns:
            Severity level: 'critical', 'high', 'medium', 'low'
        """
        critical_risks = student_metrics.get("critical_risks", 0)
        if critical_risks > 0:
            return "critical"

        ai_dependency = student_metrics.get("ai_dependency", 0)
        if ai_dependency >= 0.9:
            return "critical"
        elif ai_dependency >= self.thresholds["ai_dependency"]:
            return "high"

        high_risks = student_metrics.get("high_risks", 0)
        if high_risks >= 5:
            return "high"
        elif high_risks >= self.thresholds["high_risk_count"]:
            return "medium"

        return "low"

    def collect_evidence(
        self,
        student_metrics: Dict[str, Any]
    ) -> List[str]:
        """
        Collect evidence points for alert.

        Args:
            student_metrics: Dictionary with student risk/engagement data

        Returns:
            List of evidence strings
        """
        evidence = []

        critical_risks = student_metrics.get("critical_risks", 0)
        if critical_risks > 0:
            evidence.append(f"{critical_risks} riesgo(s) crítico(s) detectado(s)")

        ai_dependency = student_metrics.get("ai_dependency", 0)
        if ai_dependency >= self.thresholds["ai_dependency"]:
            evidence.append(f"Dependencia de IA: {ai_dependency:.0%}")

        high_risks = student_metrics.get("high_risks", 0)
        if high_risks >= self.thresholds["high_risk_count"]:
            evidence.append(f"{high_risks} riesgo(s) de nivel alto")

        sessions = student_metrics.get("sessions", 0)
        if sessions < 3 and sessions > 0:
            evidence.append(f"Bajo engagement: solo {sessions} sesiones")

        return evidence


__all__ = [
    "InstitutionalRecommendationEngine",
    "AlertGenerator",
]
