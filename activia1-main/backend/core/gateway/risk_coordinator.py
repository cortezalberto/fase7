"""
Risk Coordinator - Risk analysis management for AIGateway.

Cortez66: Extracted from ai_gateway.py (2,389 lines)

This module handles:
- Risk creation and persistence
- Risk analysis based on traces and classification
- Risk report generation

Risk Types Detected:
- RC1: Total delegation (requesting complete solutions)
- RC2: Excessive AI dependency (high ai_involvement)
- RC3: Lack of justification (decisions without explanation)
- RE1: Academic integrity (undisclosed AI use)
- REp1: Uncritical acceptance (not questioning AI responses)

All operations are STATELESS - data is persisted to PostgreSQL.
"""
import logging
import uuid
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from ...models.risk import Risk, RiskReport, RiskType, RiskLevel, RiskDimension
from ...models.trace import CognitiveTrace

if TYPE_CHECKING:
    from .protocols import RiskRepositoryProtocol

logger = logging.getLogger(__name__)


def _get_metrics():
    """Lazy import to avoid circular dependencies."""
    try:
        from ...api.routers.metrics import metrics
        return metrics
    except ImportError:
        return None


class RiskCoordinator:
    """
    Coordinates risk analysis and persistence operations.

    This class manages the creation, persistence, and retrieval of
    risks. It's designed to be STATELESS - all data is persisted
    to the database immediately.

    Attributes:
        risk_repo: Repository for risk operations
    """

    def __init__(self, risk_repo: Optional["RiskRepositoryProtocol"] = None):
        """
        Initialize the RiskCoordinator.

        Args:
            risk_repo: Repository for risk CRUD operations
        """
        self.risk_repo = risk_repo

    def create_risk(
        self,
        session_id: str,
        student_id: str,
        activity_id: str,
        risk_type: RiskType,
        risk_level: RiskLevel,
        dimension: RiskDimension,
        description: str,
        evidence: List[str],
        trace_ids: List[str],
        **kwargs
    ) -> Risk:
        """
        Create a Risk object (does not persist yet).

        Args:
            session_id: Session ID
            student_id: Student ID
            activity_id: Activity ID
            risk_type: Type of risk (COGNITIVE_DELEGATION, AI_DEPENDENCY, etc.)
            risk_level: Risk level (LOW, MEDIUM, HIGH, CRITICAL)
            dimension: Risk dimension (COGNITIVE, EPISTEMIC, etc.)
            description: Human-readable description
            evidence: List of evidence strings
            trace_ids: List of related trace IDs
            **kwargs: Additional risk fields (root_cause, recommendations, etc.)

        Returns:
            Risk object (not persisted)
        """
        return Risk(
            id=str(uuid.uuid4()),
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            risk_type=risk_type,
            risk_level=risk_level,
            dimension=dimension,
            description=description,
            evidence=evidence,
            trace_ids=trace_ids,
            **kwargs
        )

    def persist_risk(
        self,
        risk: Risk,
        flow_id: Optional[str] = None,
        risk_repo_override: Optional["RiskRepositoryProtocol"] = None,
    ) -> None:
        """
        Persist a risk to the database (STATELESS).

        Args:
            risk: Risk object to persist
            flow_id: Optional flow ID for tracing
            risk_repo_override: Optional repository to use instead of default

        Note:
            If risk_repo is None, this is a no-op for backward compatibility.
        """
        repo = risk_repo_override or self.risk_repo

        if repo is not None:
            try:
                repo.create(risk)
                logger.info(
                    "Risk persisted to database",
                    extra={
                        "risk_id": risk.id,
                        "risk_type": risk.risk_type.value,
                        "risk_level": risk.risk_level.value,
                        "dimension": risk.dimension.value,
                        "session_id": risk.session_id,
                        "flow_id": flow_id
                    }
                )
                # Record Prometheus metric for risk detection
                metrics = _get_metrics()
                if metrics:
                    metrics.record_risk_detection(
                        risk_type=risk.risk_type.value,
                        risk_level=risk.risk_level.value,
                        dimension=risk.dimension.value
                    )
            except Exception as e:
                logger.error(
                    "Failed to persist risk to database: %s: %s",
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                    extra={
                        "risk_id": risk.id,
                        "risk_type": risk.risk_type.value,
                        "session_id": risk.session_id,
                        "flow_id": flow_id
                    }
                )
        else:
            logger.warning(
                "Risk repository is None, cannot persist risk",
                extra={
                    "risk_id": risk.id,
                    "risk_type": risk.risk_type.value,
                    "flow_id": flow_id
                }
            )

    def analyze_risks(
        self,
        session_id: str,
        input_trace: CognitiveTrace,
        response_trace: CognitiveTrace,
        classification: Dict[str, Any],
        flow_id: Optional[str] = None,
        risk_repo_override: Optional["RiskRepositoryProtocol"] = None,
    ) -> List[Risk]:
        """
        Analyze risks based on traces and classification.

        Performs risk analysis from input and output traces.
        In MVP executes synchronously, in production would be async.

        Args:
            session_id: Session ID
            input_trace: Input trace (student's prompt)
            response_trace: Output trace (agent's response)
            classification: Prompt classification (type, delegation, etc.)
            flow_id: Optional flow ID for tracing
            risk_repo_override: Optional repository to use instead of default

        Returns:
            List of detected Risk objects (already persisted)

        Detects:
        - RC1: Total delegation (requests for complete code)
        - RC2: Excessive AI dependency (high ai_involvement)
        - RC3: Lack of justification (decisions without explanation)
        - REp1: Uncritical acceptance (not questioning AI responses)
        """
        logger.info(
            "Starting risk analysis",
            extra={
                "session_id": session_id,
                "input_trace_id": input_trace.id,
                "response_trace_id": response_trace.id,
                "classification_type": classification.get("type", "unknown"),
                "is_total_delegation": classification.get("is_total_delegation", False),
                "ai_involvement": input_trace.ai_involvement,
                "flow_id": flow_id
            }
        )

        # Skip if no repositories available (backward compatibility)
        if self.risk_repo is None and risk_repo_override is None:
            logger.debug(
                "Risk repository not available, skipping risk analysis",
                extra={"flow_id": flow_id, "session_id": session_id}
            )
            return []

        detected_risks = []

        # === RC1: Total Delegation ===
        if classification.get("is_total_delegation", False):
            delegation_signals = classification.get("delegation_signals", [])
            risk = self.create_risk(
                session_id=session_id,
                student_id=input_trace.student_id,
                activity_id=input_trace.activity_id,
                risk_type=RiskType.COGNITIVE_DELEGATION,
                risk_level=RiskLevel.HIGH,
                dimension=RiskDimension.COGNITIVE,
                description=(
                    "Intento de delegacion total detectado. El estudiante solicita "
                    "soluciones completas sin descomposicion del problema."
                ),
                evidence=[
                    input_trace.content[:200],  # First 200 chars of prompt
                    f"Senales: {', '.join(delegation_signals[:3])}"
                ],
                trace_ids=[input_trace.id, response_trace.id],
                root_cause="Tendencia a delegar la resolucion completa a la IA sin esfuerzo propio",
                recommendations=[
                    "Solicitar descomposicion explicita del problema en subtareas",
                    "Exigir justificacion de cada paso antes de implementar",
                    "Reducir nivel de ayuda del tutor temporalmente",
                    "Asignar ejercicios similares sin acceso a IA"
                ],
                pedagogical_intervention=(
                    "Activar modo socratico estricto: solo preguntas guia, sin pistas directas"
                )
            )
            detected_risks.append(risk)
            self.persist_risk(risk, flow_id=flow_id, risk_repo_override=risk_repo_override)

        # === RC2: Excessive AI Dependency ===
        from ..constants import AI_DEPENDENCY_MEDIUM_THRESHOLD
        if input_trace.ai_involvement > AI_DEPENDENCY_MEDIUM_THRESHOLD:
            risk = self.create_risk(
                session_id=session_id,
                student_id=input_trace.student_id,
                activity_id=input_trace.activity_id,
                risk_type=RiskType.AI_DEPENDENCY,
                risk_level=RiskLevel.MEDIUM,
                dimension=RiskDimension.COGNITIVE,
                description=(
                    f"Nivel de dependencia de IA elevado: {input_trace.ai_involvement:.1%}. "
                    "El estudiante depende excesivamente de la asistencia de IA."
                ),
                evidence=[f"AI involvement: {input_trace.ai_involvement:.2%}"],
                trace_ids=[input_trace.id],
                recommendations=[
                    "Fomentar resolucion autonoma con menos asistencia de IA",
                    "Asignar ejercicios sin acceso a IA para desarrollar autonomia",
                    "Revisar interacciones previas para identificar patron de dependencia"
                ]
            )
            detected_risks.append(risk)
            self.persist_risk(risk, flow_id=flow_id, risk_repo_override=risk_repo_override)

        # === RC3: Lack of Justification ===
        has_justification = (
            input_trace.decision_justification is not None and
            len(input_trace.decision_justification.strip()) > 20
        )
        if not has_justification and not classification.get("is_question", False):
            # Only detect if NOT a conceptual question (where justification is not expected)
            risk = self.create_risk(
                session_id=session_id,
                student_id=input_trace.student_id,
                activity_id=input_trace.activity_id,
                risk_type=RiskType.LACK_JUSTIFICATION,
                risk_level=RiskLevel.LOW,
                dimension=RiskDimension.COGNITIVE,
                description=(
                    "El estudiante no proporciona justificacion de sus decisiones o razonamiento. "
                    "Esto dificulta evaluar su proceso cognitivo."
                ),
                evidence=["No se detecto campo decision_justification"],
                trace_ids=[input_trace.id],
                recommendations=[
                    "Exigir explicitacion del razonamiento en cada interaccion",
                    "Solicitar que explique 'por que' eligio cierto enfoque",
                    "Usar prompts estructurados que incluyan seccion de justificacion"
                ]
            )
            detected_risks.append(risk)
            self.persist_risk(risk, flow_id=flow_id, risk_repo_override=risk_repo_override)

        # === REp1: Uncritical Acceptance ===
        if hasattr(response_trace, 'alternatives_considered'):
            alternatives = response_trace.alternatives_considered or []
            if len(alternatives) == 0 and input_trace.ai_involvement > 0.5:
                risk = self.create_risk(
                    session_id=session_id,
                    student_id=input_trace.student_id,
                    activity_id=input_trace.activity_id,
                    risk_type=RiskType.UNCRITICAL_ACCEPTANCE,
                    risk_level=RiskLevel.MEDIUM,
                    dimension=RiskDimension.EPISTEMIC,
                    description=(
                        "El estudiante no considera alternativas ni cuestiona las respuestas de la IA. "
                        "Esto indica posible aceptacion acritica."
                    ),
                    evidence=["No se registraron alternativas consideradas"],
                    trace_ids=[input_trace.id, response_trace.id],
                    recommendations=[
                        "Fomentar pensamiento critico: 'Que otras opciones existen?'",
                        "Solicitar comparacion entre diferentes enfoques",
                        "Pedir que identifique limitaciones de la solucion propuesta"
                    ]
                )
                detected_risks.append(risk)
                self.persist_risk(risk, flow_id=flow_id, risk_repo_override=risk_repo_override)

        # Log summary
        if detected_risks:
            logger.warning(
                "Risk analysis completed: %d risks detected",
                len(detected_risks),
                extra={
                    "session_id": session_id,
                    "risk_count": len(detected_risks),
                    "risk_types": [r.risk_type.value for r in detected_risks],
                    "risk_levels": [r.risk_level.value for r in detected_risks],
                    "flow_id": flow_id
                }
            )
        else:
            logger.info(
                "Risk analysis completed: no risks detected",
                extra={"session_id": session_id, "flow_id": flow_id}
            )

        return detected_risks

    def get_risk_report(
        self,
        student_id: str,
        activity_id: str
    ) -> Optional[RiskReport]:
        """
        Get risk report for a student-activity pair from database (STATELESS).

        Args:
            student_id: Student ID
            activity_id: Activity ID

        Returns:
            RiskReport or None if no risks found
        """
        if self.risk_repo is None:
            return None

        # Read from database
        risks = self.risk_repo.get_by_student(student_id)

        # Filter by activity_id
        risks = [r for r in risks if r.activity_id == activity_id]

        if not risks:
            return None

        # Build RiskReport
        report = RiskReport(
            id=f"report_{student_id}_{activity_id}",
            student_id=student_id,
            activity_id=activity_id
        )

        for db_risk in risks:
            risk = Risk(
                id=db_risk.id,
                student_id=db_risk.student_id,
                activity_id=db_risk.activity_id,
                risk_type=RiskType(db_risk.risk_type),
                risk_level=RiskLevel(db_risk.risk_level),
                dimension=RiskDimension(db_risk.dimension),
                description=db_risk.description or "",
                evidence=db_risk.evidence or [],
                trace_ids=db_risk.trace_ids or [],
            )
            report.add_risk(risk)

        return report
