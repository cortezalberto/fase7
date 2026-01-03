"""
Training Risk Monitor - Monitoreo de riesgos en tiempo real para el Entrenador Digital.

Cortez50: Implementa detección de patrones de riesgo durante ejercicios.
FIX Cortez52: Added TTL-based cleanup to prevent memory leaks.

Este componente detecta señales de:
- Copy-paste (velocidad de escritura imposible)
- Frustración (múltiples intentos fallidos)
- Dependencia de pistas (solicitar pista antes de intentar)
- Posible abandono

Uso:
    from backend.core.training_risk_monitor import TrainingRiskMonitor

    monitor = TrainingRiskMonitor()

    # Analizar un intento
    result = await monitor.analyze_attempt(
        session_id=session_id,
        student_id=student_id,
        exercise_id=exercise_id,
        code=codigo,
        attempt_number=3,
        time_since_last_seconds=2.5
    )
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import threading  # FIX Cortez69 HIGH-CORE-001: Thread safety

from ..constants import utc_now

logger = logging.getLogger(__name__)


class RiskType(str, Enum):
    """Tipos de riesgo detectables en entrenamiento."""
    COPY_PASTE = "copy_paste"
    FRUSTRATION = "frustration"
    HINT_DEPENDENCY = "hint_dependency"
    POSSIBLE_ABANDONMENT = "possible_abandonment"
    RAPID_SUBMISSION = "rapid_submission"


class RiskSeverity(str, Enum):
    """Severidad del riesgo detectado."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskFlag:
    """Bandera de riesgo detectado."""
    risk_type: RiskType
    severity: RiskSeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "risk_type": self.risk_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "detected_at": self.detected_at.isoformat()
        }


@dataclass
class RiskAnalysisResult:
    """Resultado del análisis de riesgos."""
    flags: List[RiskFlag] = field(default_factory=list)
    alerts: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def has_critical_risks(self) -> bool:
        return any(f.severity == RiskSeverity.CRITICAL for f in self.flags)

    @property
    def has_high_risks(self) -> bool:
        return any(f.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL] for f in self.flags)


@dataclass
class SessionRiskState:
    """Estado de riesgos acumulado para una sesión."""
    session_id: str
    student_id: str

    # Contadores
    total_attempts: int = 0
    consecutive_failures: int = 0
    hints_requested: int = 0
    attempts_since_hint: int = 0

    # Timestamps
    last_attempt_time: Optional[datetime] = None
    last_hint_time: Optional[datetime] = None
    # FIX Cortez52: Track last activity for TTL cleanup
    last_activity: datetime = field(default_factory=utc_now)

    # Historial de intentos recientes (para análisis)
    recent_attempts: List[Dict[str, Any]] = field(default_factory=list)

    # Alertas ya enviadas (evitar duplicados)
    alerts_sent: List[str] = field(default_factory=list)


class TrainingRiskMonitor:
    """
    Monitor de riesgos en tiempo real para el Entrenador Digital.

    Detecta patrones que pueden indicar:
    - Deshonestidad académica (copy-paste)
    - Problemas de aprendizaje (frustración)
    - Dependencia excesiva de ayuda
    - Posible abandono

    Configuración mediante umbrales ajustables.
    """

    def __init__(
        self,
        # Umbrales de copy-paste
        copy_paste_chars_per_second: float = 50.0,  # Imposible escribir tan rápido
        copy_paste_min_chars: int = 100,  # Mínimo de caracteres para detectar

        # Umbrales de frustración
        frustration_consecutive_failures: int = 5,
        frustration_time_window_seconds: int = 120,

        # Umbrales de dependencia de pistas
        hint_dependency_threshold: int = 3,  # Solicitar pista cada N intentos o menos
        max_hints_before_alert: int = 4,

        # Umbrales de abandono
        abandonment_inactivity_seconds: int = 600,  # 10 minutos

        # FIX Cortez52: TTL for session state cleanup
        session_ttl_seconds: int = 7200,  # 2 hours default

        # Repositorio de alertas (opcional)
        alert_repo: Optional[Any] = None
    ):
        self.copy_paste_chars_per_second = copy_paste_chars_per_second
        self.copy_paste_min_chars = copy_paste_min_chars
        self.frustration_consecutive_failures = frustration_consecutive_failures
        self.frustration_time_window_seconds = frustration_time_window_seconds
        self.hint_dependency_threshold = hint_dependency_threshold
        self.max_hints_before_alert = max_hints_before_alert
        self.abandonment_inactivity_seconds = abandonment_inactivity_seconds
        self.session_ttl_seconds = session_ttl_seconds  # FIX Cortez52
        self.alert_repo = alert_repo

        # Cache de estado de sesiones
        self._session_states: Dict[str, SessionRiskState] = {}
        # FIX Cortez69 HIGH-CORE-001: Thread-safe access to _session_states
        self._states_lock = threading.Lock()

        logger.info("TrainingRiskMonitor initialized with thresholds: "
                    "copy_paste=%.1f chars/s, frustration=%d failures, "
                    "hint_dependency=%d attempts, session_ttl=%ds",
                    copy_paste_chars_per_second,
                    frustration_consecutive_failures,
                    hint_dependency_threshold,
                    session_ttl_seconds)

    def _get_session_state(
        self,
        session_id: str,
        student_id: str
    ) -> SessionRiskState:
        """Obtiene o crea el estado de riesgo para una sesión."""
        # FIX Cortez69 HIGH-CORE-001: Thread-safe access
        with self._states_lock:
            if session_id not in self._session_states:
                self._session_states[session_id] = SessionRiskState(
                    session_id=session_id,
                    student_id=student_id
                )
            # FIX Cortez52: Update last_activity timestamp
            self._session_states[session_id].last_activity = utc_now()
            return self._session_states[session_id]

    def cleanup_expired_sessions(self) -> int:
        """
        FIX Cortez52: Remove sessions that have been inactive beyond TTL.

        Returns:
            Number of sessions cleaned up
        """
        # FIX Cortez69 HIGH-CORE-001: Thread-safe access
        with self._states_lock:
            now = utc_now()
            ttl = timedelta(seconds=self.session_ttl_seconds)
            expired_sessions = [
                session_id for session_id, state in self._session_states.items()
                if (now - state.last_activity) > ttl
            ]

            for session_id in expired_sessions:
                del self._session_states[session_id]

        if expired_sessions:
            logger.info(
                "Cleaned up %d expired session states (TTL: %ds)",
                len(expired_sessions),
                self.session_ttl_seconds
            )

        return len(expired_sessions)

    def get_active_sessions_count(self) -> int:
        """FIX Cortez52: Return count of active session states for monitoring."""
        # FIX Cortez69 HIGH-CORE-001: Thread-safe access
        with self._states_lock:
            return len(self._session_states)

    async def analyze_attempt(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        attempt_number: int,
        time_since_last_seconds: Optional[float] = None,
        test_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analiza un intento de código en busca de riesgos.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            code: Código enviado
            attempt_number: Número de intento
            time_since_last_seconds: Tiempo desde el último intento
            test_result: Resultado de los tests (opcional)

        Returns:
            Diccionario con flags y alerts
        """
        state = self._get_session_state(session_id, student_id)
        result = RiskAnalysisResult()
        now = utc_now()

        # Actualizar estado
        state.total_attempts += 1

        # Análisis 1: Copy-paste
        if time_since_last_seconds is not None:
            copy_paste_risk = self._detect_copy_paste(
                code=code,
                time_since_last_seconds=time_since_last_seconds,
                state=state
            )
            if copy_paste_risk:
                result.flags.append(copy_paste_risk)

        # Análisis 2: Frustración
        if test_result:
            tests_passed = test_result.get("tests_passed", 0)
            tests_total = test_result.get("tests_total", 1)

            if tests_passed < tests_total:
                state.consecutive_failures += 1
            else:
                state.consecutive_failures = 0

            frustration_risk = self._detect_frustration(state, now)
            if frustration_risk:
                result.flags.append(frustration_risk)

        # Análisis 3: Envío muy rápido (sin pensar)
        if time_since_last_seconds is not None and time_since_last_seconds < 3.0:
            result.flags.append(RiskFlag(
                risk_type=RiskType.RAPID_SUBMISSION,
                severity=RiskSeverity.LOW,
                message="Envío muy rápido - posible prueba sin reflexión",
                details={"seconds_since_last": time_since_last_seconds}
            ))

        # Actualizar historial
        state.recent_attempts.append({
            "attempt_number": attempt_number,
            "code_length": len(code),
            "time_since_last": time_since_last_seconds,
            "success": test_result.get("tests_passed", 0) == test_result.get("tests_total", 1) if test_result else False,
            "timestamp": now.isoformat()
        })

        # Mantener solo los últimos 10 intentos
        if len(state.recent_attempts) > 10:
            state.recent_attempts = state.recent_attempts[-10:]

        state.last_attempt_time = now
        state.attempts_since_hint += 1

        # Generar alertas para riesgos HIGH/CRITICAL
        for flag in result.flags:
            if flag.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]:
                alert_key = f"{flag.risk_type.value}_{exercise_id}"
                if alert_key not in state.alerts_sent:
                    result.alerts.append(flag.message)
                    state.alerts_sent.append(alert_key)

                    # Persistir alerta si hay repositorio
                    if self.alert_repo:
                        await self._persist_alert(
                            session_id=session_id,
                            student_id=student_id,
                            exercise_id=exercise_id,
                            flag=flag
                        )

        # Generar recomendaciones
        result.recommendations = self._generate_recommendations(result.flags, state)

        logger.info(
            "Risk analysis completed",
            extra={
                "session_id": session_id,
                "risks_detected": len(result.flags),
                "alerts_generated": len(result.alerts)
            }
        )

        return {
            "flags": [f.to_dict() for f in result.flags],
            "alerts": result.alerts,
            "recommendations": result.recommendations,
            "has_critical": result.has_critical_risks,
            "has_high": result.has_high_risks
        }

    async def record_hint_request(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        hint_number: int
    ) -> Dict[str, Any]:
        """
        Registra una solicitud de pista y analiza dependencia.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            hint_number: Número de pista solicitada

        Returns:
            Diccionario con flags de dependencia si aplica
        """
        state = self._get_session_state(session_id, student_id)
        result = RiskAnalysisResult()
        now = utc_now()

        state.hints_requested += 1
        state.last_hint_time = now

        # Detectar dependencia de pistas
        if state.attempts_since_hint <= self.hint_dependency_threshold:
            severity = RiskSeverity.MEDIUM
            if state.hints_requested >= self.max_hints_before_alert:
                severity = RiskSeverity.HIGH

            result.flags.append(RiskFlag(
                risk_type=RiskType.HINT_DEPENDENCY,
                severity=severity,
                message=f"Solicitud frecuente de pistas ({state.hints_requested} pistas, "
                        f"último intento hace {state.attempts_since_hint} intentos)",
                details={
                    "hints_requested": state.hints_requested,
                    "attempts_since_last_hint": state.attempts_since_hint,
                    "hint_number": hint_number
                }
            ))

        # Resetear contador de intentos desde última pista
        state.attempts_since_hint = 0

        # Generar alertas
        for flag in result.flags:
            if flag.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]:
                alert_key = f"hint_dependency_{exercise_id}"
                if alert_key not in state.alerts_sent:
                    result.alerts.append(flag.message)
                    state.alerts_sent.append(alert_key)

        return {
            "flags": [f.to_dict() for f in result.flags],
            "alerts": result.alerts,
            "hint_dependency_detected": len(result.flags) > 0
        }

    def _detect_copy_paste(
        self,
        code: str,
        time_since_last_seconds: float,
        state: SessionRiskState
    ) -> Optional[RiskFlag]:
        """
        Detecta posible copy-paste basado en velocidad de escritura.

        Si el estudiante envía N caracteres en T segundos, y N/T supera
        el umbral humano posible (~50 chars/s), es copy-paste.
        """
        if not state.recent_attempts:
            return None

        # Obtener código del intento anterior
        last_attempt = state.recent_attempts[-1]
        previous_length = last_attempt.get("code_length", 0)

        # Calcular caracteres nuevos
        chars_added = len(code) - previous_length

        # Solo analizar si se agregaron suficientes caracteres
        if chars_added < self.copy_paste_min_chars:
            return None

        # Evitar división por cero
        if time_since_last_seconds < 0.1:
            time_since_last_seconds = 0.1

        # Calcular velocidad de escritura
        chars_per_second = chars_added / time_since_last_seconds

        if chars_per_second > self.copy_paste_chars_per_second:
            severity = RiskSeverity.HIGH
            if chars_per_second > self.copy_paste_chars_per_second * 2:
                severity = RiskSeverity.CRITICAL

            return RiskFlag(
                risk_type=RiskType.COPY_PASTE,
                severity=severity,
                message=f"Posible copy-paste detectado: {int(chars_added)} caracteres "
                        f"en {time_since_last_seconds:.1f} segundos "
                        f"({int(chars_per_second)} chars/s)",
                details={
                    "chars_added": chars_added,
                    "time_seconds": time_since_last_seconds,
                    "chars_per_second": round(chars_per_second, 1),
                    "threshold": self.copy_paste_chars_per_second
                }
            )

        return None

    def _detect_frustration(
        self,
        state: SessionRiskState,
        now: datetime
    ) -> Optional[RiskFlag]:
        """
        Detecta patrón de frustración.

        Múltiples intentos fallidos en poco tiempo.
        """
        if state.consecutive_failures < self.frustration_consecutive_failures:
            return None

        # Verificar si están dentro de la ventana de tiempo
        if state.last_attempt_time:
            recent_attempts = [
                a for a in state.recent_attempts
                if not a.get("success", False)
            ]

            if len(recent_attempts) >= self.frustration_consecutive_failures:
                # Verificar ventana de tiempo
                first_failure_time = datetime.fromisoformat(
                    recent_attempts[-self.frustration_consecutive_failures]["timestamp"]
                )
                time_window = (now - first_failure_time).total_seconds()

                if time_window <= self.frustration_time_window_seconds:
                    severity = RiskSeverity.MEDIUM
                    if state.consecutive_failures >= self.frustration_consecutive_failures * 1.5:
                        severity = RiskSeverity.HIGH

                    return RiskFlag(
                        risk_type=RiskType.FRUSTRATION,
                        severity=severity,
                        message=f"Patrón de frustración detectado: "
                                f"{state.consecutive_failures} intentos fallidos "
                                f"en {int(time_window)} segundos",
                        details={
                            "consecutive_failures": state.consecutive_failures,
                            "time_window_seconds": int(time_window),
                            "threshold_failures": self.frustration_consecutive_failures
                        }
                    )

        return None

    def _generate_recommendations(
        self,
        flags: List[RiskFlag],
        state: SessionRiskState
    ) -> List[str]:
        """Genera recomendaciones basadas en los riesgos detectados."""
        recommendations = []

        for flag in flags:
            if flag.risk_type == RiskType.COPY_PASTE:
                recommendations.append(
                    "Intenta escribir el código por tu cuenta para consolidar el aprendizaje"
                )
            elif flag.risk_type == RiskType.FRUSTRATION:
                recommendations.append(
                    "Considera tomar un descanso o pedir una pista para reorientar tu enfoque"
                )
            elif flag.risk_type == RiskType.HINT_DEPENDENCY:
                recommendations.append(
                    "Intenta hacer más intentos antes de solicitar la siguiente pista"
                )
            elif flag.risk_type == RiskType.RAPID_SUBMISSION:
                recommendations.append(
                    "Toma unos segundos para revisar tu código antes de enviar"
                )

        return recommendations

    async def _persist_alert(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        flag: RiskFlag
    ) -> None:
        """Persiste una alerta en el repositorio."""
        if not self.alert_repo:
            return

        try:
            alert_data = {
                "session_id": session_id,
                "student_id": student_id,
                "exercise_id": exercise_id,
                "alert_type": f"training_{flag.risk_type.value}",
                "severity": flag.severity.value,
                "message": flag.message,
                "details": flag.details,
                "created_at": flag.detected_at
            }
            self.alert_repo.create(alert_data)
        except Exception as e:
            logger.error("Failed to persist alert: %s", e)

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene resumen de riesgos de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Diccionario con resumen de riesgos
        """
        # FIX Cortez70 CRIT-CORE-001: Thread-safe access to _session_states
        with self._states_lock:
            if session_id not in self._session_states:
                return {"error": "Session not found"}

            state = self._session_states[session_id]

            return {
                "session_id": session_id,
                "student_id": state.student_id,
                "total_attempts": state.total_attempts,
                "hints_requested": state.hints_requested,
                "consecutive_failures": state.consecutive_failures,
                "alerts_sent": list(state.alerts_sent),  # Copy to avoid mutation
                "recent_attempts_count": len(state.recent_attempts)
            }

    def clear_session(self, session_id: str) -> None:
        """Limpia el estado de una sesión (al finalizar)."""
        # FIX Cortez70 CRIT-CORE-002: Thread-safe access to _session_states
        with self._states_lock:
            if session_id in self._session_states:
                del self._session_states[session_id]
                logger.debug("Cleared risk state for session %s", session_id)
