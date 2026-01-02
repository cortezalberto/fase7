"""
Training Trace Collector - Captura de trazas N4 para el Entrenador Digital.

Cortez50: Implementa la captura de trazabilidad cognitiva para ejercicios.
FIX Cortez52: Added TTL-based cleanup to prevent memory leaks in _attempt_cache.

Este componente traduce los eventos del Entrenador Digital al modelo de
trazabilidad N4 del sistema. Implementa heurísticas para inferir el estado
cognitivo a partir de señales observables.

Estrategias de trazabilidad:
- Estrategia A: Inferida (pasiva) - Deduce estado cognitivo de patrones
- Estrategia B: Explícita opcional (semi-activa) - Captura voluntaria
- Estrategia C: Reflexión post-ejercicio (activa) - Al completar

Uso:
    from backend.core.training_traceability import TrainingTraceCollector

    collector = TrainingTraceCollector(
        trace_repo=trace_repo,
        sequence_repo=sequence_repo
    )

    # Capturar intento de código
    trace = await collector.trace_code_attempt(
        session_id=session_id,
        student_id=student_id,
        exercise_id=exercise_id,
        code=codigo,
        result=sandbox_result,
        attempt_number=1,
        previous_code=None
    )
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid
import difflib

from .constants import utc_now

logger = logging.getLogger(__name__)


class InferredCognitiveState(str, Enum):
    """Estados cognitivos inferidos para el Entrenador Digital."""
    EXPLORACION = "exploracion"
    IMPLEMENTACION = "implementacion"
    DEPURACION = "depuracion"
    CAMBIO_ESTRATEGIA = "cambio_estrategia"
    VALIDACION = "validacion"
    BUSQUEDA_AYUDA = "busqueda_ayuda"
    COMPRENSION_LOGRADA = "comprension_lograda"
    ATASCADO = "atascado"
    REFLEXION = "reflexion"
    ABANDONO = "abandono"


class InferenceConfidence(str, Enum):
    """Nivel de confianza en la inferencia del estado cognitivo."""
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


@dataclass
class CognitiveInference:
    """Resultado de la inferencia de estado cognitivo."""
    state: InferredCognitiveState
    confidence: InferenceConfidence
    confidence_score: float  # 0.0 - 1.0
    reasoning: str  # Por qué se infirió este estado
    signals: List[str] = field(default_factory=list)  # Señales que llevaron a la inferencia


@dataclass
class TrainingTraceData:
    """Datos de una traza de entrenamiento."""
    id: str
    session_id: str
    student_id: str
    exercise_id: str
    trace_type: str  # "code_attempt", "hint_request", "reflection", "session_start"
    cognitive_state: str
    inference_confidence: float
    content: str
    context: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class TrainingTraceCollector:
    """
    Colector de trazas N4 para el Entrenador Digital.

    Responsabilidades:
    1. Inferir estado cognitivo de señales observables
    2. Crear trazas N4 compatibles con el sistema de trazabilidad
    3. Gestionar secuencias de trazas por sesión
    4. Calcular métricas de proceso
    """

    def __init__(
        self,
        trace_repo: Optional[Any] = None,
        sequence_repo: Optional[Any] = None,
        # FIX Cortez52: TTL for cache cleanup
        cache_ttl_seconds: int = 7200  # 2 hours default
    ):
        """
        Inicializa el colector.

        Args:
            trace_repo: Repositorio de trazas (opcional para modo standalone)
            sequence_repo: Repositorio de secuencias (opcional)
            cache_ttl_seconds: TTL para limpieza automática del cache (FIX Cortez52)
        """
        self.trace_repo = trace_repo
        self.sequence_repo = sequence_repo
        self.cache_ttl_seconds = cache_ttl_seconds  # FIX Cortez52

        # Cache de intentos por sesión para análisis de diff
        self._attempt_cache: Dict[str, List[Dict[str, Any]]] = {}
        # FIX Cortez52: Track last activity per session for TTL cleanup
        self._session_last_activity: Dict[str, datetime] = {}

        logger.info("TrainingTraceCollector initialized with cache_ttl=%ds", cache_ttl_seconds)

    def _update_session_activity(self, session_id: str) -> None:
        """FIX Cortez52: Update last activity timestamp for a session."""
        self._session_last_activity[session_id] = utc_now()

    def cleanup_expired_sessions(self) -> int:
        """
        FIX Cortez52: Remove sessions that have been inactive beyond TTL.

        Returns:
            Number of sessions cleaned up
        """
        now = utc_now()
        ttl = timedelta(seconds=self.cache_ttl_seconds)
        expired_sessions = [
            session_id for session_id, last_activity in self._session_last_activity.items()
            if (now - last_activity) > ttl
        ]

        for session_id in expired_sessions:
            if session_id in self._attempt_cache:
                del self._attempt_cache[session_id]
            del self._session_last_activity[session_id]

        if expired_sessions:
            logger.info(
                "Cleaned up %d expired session caches (TTL: %ds)",
                len(expired_sessions),
                self.cache_ttl_seconds
            )

        return len(expired_sessions)

    def get_active_sessions_count(self) -> int:
        """FIX Cortez52: Return count of active session caches for monitoring."""
        return len(self._attempt_cache)

    def clear_session_cache(self, session_id: str) -> None:
        """FIX Cortez52: Clear cache for a specific session (call when session ends)."""
        if session_id in self._attempt_cache:
            del self._attempt_cache[session_id]
        if session_id in self._session_last_activity:
            del self._session_last_activity[session_id]
        logger.debug("Cleared trace cache for session %s", session_id)

    async def create_session_sequence(
        self,
        session_id: str,
        student_id: str,
        activity_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea una secuencia de trazas para una sesión de entrenamiento.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            activity_type: Tipo de actividad ("training")
            metadata: Metadata adicional (language, unit, exercises)

        Returns:
            Diccionario con id de la secuencia
        """
        sequence_id = str(uuid.uuid4())

        # Inicializar cache para la sesión
        self._attempt_cache[session_id] = []
        self._update_session_activity(session_id)  # FIX Cortez52

        sequence_data = {
            "id": sequence_id,
            "session_id": session_id,
            "student_id": student_id,
            "activity_type": activity_type,
            "metadata": metadata or {},
            "start_time": utc_now().isoformat(),
            "traces": []
        }

        # Persistir si hay repositorio
        if self.sequence_repo:
            try:
                self.sequence_repo.create(sequence_data)
            except Exception as e:
                logger.error("Failed to persist sequence: %s", e)

        logger.info(
            "Created trace sequence",
            extra={
                "sequence_id": sequence_id,
                "session_id": session_id
            }
        )

        return {"id": sequence_id, **sequence_data}

    async def trace_code_attempt(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        result: Dict[str, Any],
        attempt_number: int,
        previous_code: Optional[str] = None,
        time_since_last_seconds: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Captura una traza de intento de código.

        Analiza el código enviado y el resultado para inferir el estado
        cognitivo del estudiante.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            code: Código enviado
            result: Resultado del sandbox (tests)
            attempt_number: Número de intento
            previous_code: Código del intento anterior
            time_since_last_seconds: Segundos desde el último intento

        Returns:
            Diccionario con trace_id, cognitive_state_inferred, inference_confidence
        """
        trace_id = str(uuid.uuid4())

        # Inferir estado cognitivo
        inference = self._infer_cognitive_state(
            code=code,
            result=result,
            attempt_number=attempt_number,
            previous_code=previous_code,
            session_history=self._attempt_cache.get(session_id, [])
        )

        # Calcular diff si hay código anterior
        code_diff = None
        if previous_code:
            code_diff = self._calculate_code_diff(previous_code, code)

        # Crear datos de traza
        trace_data = TrainingTraceData(
            id=trace_id,
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            trace_type="code_attempt",
            cognitive_state=inference.state.value,
            inference_confidence=inference.confidence_score,
            content=code[:500] if len(code) > 500 else code,  # Truncar para almacenamiento
            context={
                "attempt_number": attempt_number,
                "tests_passed": result.get("tests_passed", 0),
                "tests_total": result.get("tests_total", 0),
                "exit_code": result.get("exit_code", -1),
                "code_length": len(code),
                "code_diff": code_diff,
                "time_since_last_seconds": time_since_last_seconds
            },
            created_at=utc_now(),
            metadata={
                "inference_reasoning": inference.reasoning,
                "inference_signals": inference.signals,
                "confidence_level": inference.confidence.value
            }
        )

        # Actualizar cache de la sesión
        if session_id not in self._attempt_cache:
            self._attempt_cache[session_id] = []

        self._attempt_cache[session_id].append({
            "trace_id": trace_id,
            "code": code,
            "result": result,
            "attempt_number": attempt_number,
            "cognitive_state": inference.state.value,
            "timestamp": trace_data.created_at.isoformat()
        })
        self._update_session_activity(session_id)  # FIX Cortez52

        # Persistir si hay repositorio
        if self.trace_repo:
            try:
                self._persist_trace(trace_data)
            except Exception as e:
                logger.error("Failed to persist trace: %s", e)

        logger.info(
            "Captured code attempt trace",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "cognitive_state": inference.state.value,
                "confidence": inference.confidence_score
            }
        )

        return {
            "trace_id": trace_id,
            "cognitive_state_inferred": inference.state.value,
            "inference_confidence": inference.confidence_score,
            "inference_reasoning": inference.reasoning
        }

    async def trace_hint_request(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        hint_number: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Captura una traza de solicitud de pista.

        El estado cognitivo es siempre BUSQUEDA_AYUDA con alta confianza.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            hint_number: Número de pista solicitada
            reason: Razón opcional (si el estudiante la proporcionó)

        Returns:
            Diccionario con trace_id
        """
        trace_id = str(uuid.uuid4())

        trace_data = TrainingTraceData(
            id=trace_id,
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            trace_type="hint_request",
            cognitive_state=InferredCognitiveState.BUSQUEDA_AYUDA.value,
            inference_confidence=0.95,  # Alta confianza - acción explícita
            content=reason or f"Solicitud de pista nivel {hint_number + 1}",
            context={
                "hint_number": hint_number,
                "explicit_reason": reason is not None
            },
            created_at=utc_now(),
            metadata={
                "inference_reasoning": "Acción explícita de solicitar ayuda",
                "confidence_level": InferenceConfidence.ALTA.value
            }
        )

        # Actualizar cache
        if session_id in self._attempt_cache:
            self._attempt_cache[session_id].append({
                "trace_id": trace_id,
                "type": "hint_request",
                "hint_number": hint_number,
                "cognitive_state": InferredCognitiveState.BUSQUEDA_AYUDA.value,
                "timestamp": trace_data.created_at.isoformat()
            })
            self._update_session_activity(session_id)  # FIX Cortez52

        # Persistir
        if self.trace_repo:
            try:
                self._persist_trace(trace_data)
            except Exception as e:
                logger.error("Failed to persist hint trace: %s", e)

        return {"trace_id": trace_id}

    async def trace_reflection(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        content: str,
        decision_justification: str,
        alternatives_considered: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Captura una traza de reflexión post-ejercicio.

        Es la traza más rica porque contiene justificaciones explícitas
        del estudiante.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            content: Respuesta a "¿Cómo lo resolviste?"
            decision_justification: Respuesta a "¿Qué aprendiste?"
            alternatives_considered: Alternativas que consideró
            context: Contexto adicional (dificultad, errores)

        Returns:
            Diccionario con trace_id
        """
        trace_id = str(uuid.uuid4())

        trace_data = TrainingTraceData(
            id=trace_id,
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            trace_type="reflection",
            cognitive_state=InferredCognitiveState.REFLEXION.value,
            inference_confidence=1.0,  # Máxima confianza - contenido explícito
            content=content,
            context={
                "decision_justification": decision_justification,
                "alternatives_considered": alternatives_considered,
                **context
            },
            created_at=utc_now(),
            metadata={
                "inference_reasoning": "Reflexión explícita del estudiante",
                "confidence_level": InferenceConfidence.ALTA.value,
                "explicit_content": True
            }
        )

        # Persistir
        if self.trace_repo:
            try:
                self._persist_trace(trace_data)
            except Exception as e:
                logger.error("Failed to persist reflection trace: %s", e)

        logger.info(
            "Captured reflection trace",
            extra={
                "trace_id": trace_id,
                "session_id": session_id,
                "has_alternatives": len(alternatives_considered) > 0
            }
        )

        return {"trace_id": trace_id}

    async def get_process_analysis(
        self,
        session_id: str,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene análisis del proceso de resolución.

        Reconstruye el camino cognitivo y calcula métricas.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante

        Returns:
            Diccionario con análisis completo
        """
        # Obtener historial de la sesión
        history = self._attempt_cache.get(session_id, [])

        if not history:
            return {
                "session_id": session_id,
                "total_events": 0,
                "cognitive_path": [],
                "metrics": {},
                "recommendations": []
            }

        # Reconstruir camino cognitivo
        cognitive_path = [
            {
                "timestamp": entry.get("timestamp"),
                "state": entry.get("cognitive_state"),
                "type": entry.get("type", "code_attempt")
            }
            for entry in history
        ]

        # Calcular métricas
        total_attempts = len([e for e in history if e.get("type") != "hint_request"])
        hints_used = len([e for e in history if e.get("type") == "hint_request"])

        # Detectar cambios de estrategia
        strategy_changes = self._count_strategy_changes(history)

        # Calcular autonomía
        autonomy_score = self._calculate_autonomy_score(total_attempts, hints_used)

        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            total_attempts=total_attempts,
            hints_used=hints_used,
            strategy_changes=strategy_changes,
            autonomy_score=autonomy_score
        )

        return {
            "session_id": session_id,
            "total_events": len(history),
            "cognitive_path": cognitive_path,
            "metrics": {
                "total_attempts": total_attempts,
                "hints_used": hints_used,
                "strategy_changes": strategy_changes,
                "autonomy_score": round(autonomy_score, 2)
            },
            "recommendations": recommendations
        }

    def _infer_cognitive_state(
        self,
        code: str,
        result: Dict[str, Any],
        attempt_number: int,
        previous_code: Optional[str],
        session_history: List[Dict[str, Any]]
    ) -> CognitiveInference:
        """
        Infiere el estado cognitivo del estudiante.

        Implementa la Estrategia A (trazabilidad inferida) de la propuesta.
        """
        signals = []
        tests_passed = result.get("tests_passed", 0)
        tests_total = result.get("tests_total", 1)
        exit_code = result.get("exit_code", -1)

        # Caso 1: Éxito completo
        if tests_passed == tests_total and exit_code == 0:
            signals.append("Todos los tests pasaron")
            return CognitiveInference(
                state=InferredCognitiveState.VALIDACION,
                confidence=InferenceConfidence.ALTA,
                confidence_score=0.95,
                reasoning="El código pasó todos los tests, indicando validación exitosa",
                signals=signals
            )

        # Caso 2: Primer intento
        if attempt_number == 1:
            signals.append("Primer intento del ejercicio")
            return CognitiveInference(
                state=InferredCognitiveState.EXPLORACION,
                confidence=InferenceConfidence.ALTA,
                confidence_score=0.9,
                reasoning="Primer intento, estudiante explorando el problema",
                signals=signals
            )

        # Caso 3: Con código anterior, analizar cambios
        if previous_code:
            diff = self._calculate_code_diff(previous_code, code)

            # Cambio significativo de estructura
            if diff.get("structural_change", False):
                signals.append("Cambio estructural significativo en el código")
                return CognitiveInference(
                    state=InferredCognitiveState.CAMBIO_ESTRATEGIA,
                    confidence=InferenceConfidence.MEDIA,
                    confidence_score=0.7,
                    reasoning="El código cambió significativamente, sugiriendo cambio de enfoque",
                    signals=signals
                )

            # Cambio pequeño (posible depuración)
            if diff.get("lines_changed", 0) < 5:
                signals.append("Cambio menor en el código")
                return CognitiveInference(
                    state=InferredCognitiveState.DEPURACION,
                    confidence=InferenceConfidence.MEDIA,
                    confidence_score=0.75,
                    reasoning="Cambio pequeño sugiere corrección de error específico",
                    signals=signals
                )

        # Caso 4: Múltiples intentos fallidos (posible atascamiento)
        recent_failures = self._count_recent_failures(session_history)
        if recent_failures >= 3:
            signals.append(f"{recent_failures} intentos fallidos recientes")
            return CognitiveInference(
                state=InferredCognitiveState.ATASCADO,
                confidence=InferenceConfidence.ALTA,
                confidence_score=0.85,
                reasoning=f"Múltiples intentos fallidos ({recent_failures}) sugieren atascamiento",
                signals=signals
            )

        # Caso 5: Default - Implementación en progreso
        signals.append("Código en desarrollo")
        return CognitiveInference(
            state=InferredCognitiveState.IMPLEMENTACION,
            confidence=InferenceConfidence.MEDIA,
            confidence_score=0.6,
            reasoning="Sin señales claras, asumiendo implementación en progreso",
            signals=signals
        )

    def _calculate_code_diff(
        self,
        old_code: str,
        new_code: str
    ) -> Dict[str, Any]:
        """Calcula diferencias entre dos versiones de código."""
        old_lines = old_code.splitlines()
        new_lines = new_code.splitlines()

        differ = difflib.unified_diff(old_lines, new_lines, lineterm='')
        diff_lines = list(differ)

        # Contar líneas cambiadas
        added = len([l for l in diff_lines if l.startswith('+')])
        removed = len([l for l in diff_lines if l.startswith('-')])

        # Detectar cambio estructural (más del 50% del código cambió)
        total_lines = max(len(old_lines), len(new_lines))
        change_ratio = (added + removed) / (total_lines * 2) if total_lines > 0 else 0

        return {
            "lines_added": added,
            "lines_removed": removed,
            "lines_changed": added + removed,
            "change_ratio": round(change_ratio, 2),
            "structural_change": change_ratio > 0.5
        }

    def _count_recent_failures(
        self,
        history: List[Dict[str, Any]],
        window: int = 5
    ) -> int:
        """Cuenta intentos fallidos recientes."""
        recent = history[-window:] if len(history) >= window else history
        failures = 0

        for entry in recent:
            result = entry.get("result", {})
            if result.get("tests_passed", 0) < result.get("tests_total", 1):
                failures += 1

        return failures

    def _count_strategy_changes(self, history: List[Dict[str, Any]]) -> int:
        """Cuenta cambios de estrategia detectados."""
        changes = 0
        for entry in history:
            if entry.get("cognitive_state") == InferredCognitiveState.CAMBIO_ESTRATEGIA.value:
                changes += 1
        return changes

    def _calculate_autonomy_score(
        self,
        total_attempts: int,
        hints_used: int
    ) -> float:
        """
        Calcula score de autonomía (0.0 - 1.0).

        Mayor score = más autonomía (menos dependencia de pistas).

        FIX Cortez52: Return 0.0 for zero attempts (no evidence of autonomy).
        """
        if total_attempts == 0:
            return 0.0  # FIX Cortez52: No attempts = no autonomy evidence

        # Ratio de intentos sin pista
        ratio = 1.0 - (hints_used / total_attempts)

        # Ajustar: muchas pistas penaliza más
        if hints_used > 3:
            ratio *= 0.8

        return max(0.0, min(1.0, ratio))

    def _generate_recommendations(
        self,
        total_attempts: int,
        hints_used: int,
        strategy_changes: int,
        autonomy_score: float
    ) -> List[str]:
        """Genera recomendaciones basadas en métricas."""
        recommendations = []

        if autonomy_score < 0.5:
            recommendations.append(
                "Intenta resolver más problemas sin pistas para desarrollar autonomía"
            )

        if strategy_changes == 0 and total_attempts > 3:
            recommendations.append(
                "Considera probar enfoques diferentes si tu estrategia actual no funciona"
            )

        if hints_used == 0 and total_attempts > 5:
            recommendations.append(
                "No dudes en pedir pistas cuando estés atascado - son parte del aprendizaje"
            )

        if not recommendations:
            recommendations.append(
                "Buen progreso. Sigue practicando para consolidar lo aprendido"
            )

        return recommendations

    def _persist_trace(self, trace_data: TrainingTraceData) -> None:
        """Persiste una traza en el repositorio."""
        if not self.trace_repo:
            return

        # Convertir a formato compatible con CognitiveTraceDB
        trace_dict = {
            "id": trace_data.id,
            "session_id": trace_data.session_id,
            "student_id": trace_data.student_id,
            "activity_id": trace_data.exercise_id,
            "trace_level": "n4_cognitivo",
            "interaction_type": f"training_{trace_data.trace_type}",
            "content": trace_data.content,
            "context": trace_data.context,
            "cognitive_state": trace_data.cognitive_state,
            "ai_involvement": 0.0,  # Entrenador tiene baja involucración IA
            "trace_metadata": trace_data.metadata,
            "created_at": trace_data.created_at
        }

        self.trace_repo.create(trace_dict)

    def clear_session_cache(self, session_id: str) -> None:
        """Limpia el cache de una sesión (al finalizar)."""
        if session_id in self._attempt_cache:
            del self._attempt_cache[session_id]
            logger.debug("Cleared cache for session %s", session_id)
