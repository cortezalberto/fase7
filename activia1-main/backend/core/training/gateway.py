"""
Training Gateway - Orquestador para integrar el Entrenador Digital con agentes.

Cortez50: Implementa la propuesta de integración del Entrenador Digital con el
ecosistema de agentes (T-IA-Cog, TC-N4, AR-IA).

Este componente actúa como intermediario entre los endpoints del Entrenador Digital
y el ecosistema de agentes. No reemplaza la lógica existente; la envuelve.

Arquitectura:
    Solicitud → TrainingGateway → [¿Qué necesita?]
                                       │
                       ┌───────────────┼───────────────┐
                       ▼               ▼               ▼
                 ¿Trazabilidad?  ¿Análisis de    ¿Pista
                                 riesgos?        contextual?
                       │               │               │
                       ▼               ▼               ▼
                  TC-N4 Agent    AR-IA Agent    T-IA-Cog

Uso:
    from backend.core.training_gateway import TrainingGateway

    gateway = TrainingGateway(
        trace_collector=trace_collector,
        risk_monitor=risk_monitor,
        hints_strategy=hints_strategy,
        llm_provider=llm_provider
    )

    # Al enviar código
    result = await gateway.process_code_submission(
        session_id=session_id,
        student_id=student_id,
        exercise_id=exercise_id,
        code=codigo,
        sandbox_result=sandbox_result
    )
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import logging
import asyncio

from ..constants import utc_now

logger = logging.getLogger(__name__)


@dataclass
class TrainingGatewayConfig:
    """Configuración del TrainingGateway."""

    # Feature flags (se leen de variables de entorno)
    use_tutor_hints: bool = False
    enable_n4_tracing: bool = False
    enable_risk_monitor: bool = False

    # Timeouts
    hint_generation_timeout: float = 3.0  # segundos
    trace_capture_timeout: float = 1.0
    risk_analysis_timeout: float = 2.0

    # Umbrales de riesgo
    copy_paste_threshold_chars_per_second: float = 50.0  # Imposible escribir tan rápido
    frustration_threshold_attempts: int = 5
    frustration_window_seconds: int = 120
    hint_dependency_threshold: int = 3  # Pedir pista cada N intentos


@dataclass
class CodeSubmissionResult:
    """Resultado del procesamiento de envío de código."""

    # Resultado original del evaluador
    evaluation_result: Dict[str, Any]

    # Trazabilidad N4
    trace_id: Optional[str] = None
    cognitive_state_inferred: Optional[str] = None
    inference_confidence: float = 0.0

    # Análisis de riesgos
    risk_flags: List[Dict[str, Any]] = field(default_factory=list)
    risk_alerts: List[str] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0
    features_used: List[str] = field(default_factory=list)


@dataclass
class HintRequestResult:
    """Resultado del procesamiento de solicitud de pista."""

    # Contenido de la pista
    hint_content: str
    hint_number: int
    total_hints: int

    # Trazabilidad
    trace_id: Optional[str] = None

    # Metadata
    source: str = "static"  # "static" | "tutor_ai" | "fallback"
    generation_time_ms: float = 0.0
    help_level: Optional[str] = None


class TrainingGateway:
    """
    Orquestador para integrar el Entrenador Digital con agentes.

    Responsabilidades:
    1. Coordinar la captura de trazas N4 durante ejercicios
    2. Invocar T-IA-Cog para pistas contextuales
    3. Monitorear riesgos en tiempo real
    4. Mantener compatibilidad con flujo existente
    """

    def __init__(
        self,
        trace_collector: Optional["TrainingTraceCollector"] = None,
        risk_monitor: Optional["TrainingRiskMonitor"] = None,
        hints_strategy: Optional["TrainingHintsStrategy"] = None,
        llm_provider: Optional[Any] = None,
        config: Optional[TrainingGatewayConfig] = None
    ):
        """
        Inicializa el gateway.

        Args:
            trace_collector: Colector de trazas N4 para entrenamiento
            risk_monitor: Monitor de riesgos en tiempo real
            hints_strategy: Estrategia de pistas contextuales (T-IA-Cog)
            llm_provider: Proveedor de LLM para pistas contextuales
            config: Configuración del gateway
        """
        self.trace_collector = trace_collector
        self.risk_monitor = risk_monitor
        self.hints_strategy = hints_strategy
        self.llm_provider = llm_provider
        self.config = config or TrainingGatewayConfig()

        logger.info(
            "TrainingGateway initialized with features: "
            "tracing=%s, risk_monitor=%s, tutor_hints=%s",
            self.config.enable_n4_tracing,
            self.config.enable_risk_monitor,
            self.config.use_tutor_hints
        )

    def _validate_input(
        self,
        **kwargs
    ) -> None:
        """
        FIX Cortez68 (MEDIUM): Validate input parameters.

        Raises:
            ValueError: If any parameter is invalid
        """
        for name, value in kwargs.items():
            if value is None and name not in ("previous_code", "time_since_last_seconds", "evaluation_result"):
                raise ValueError(f"Required parameter '{name}' cannot be None")
            if isinstance(value, str) and name in ("session_id", "student_id", "exercise_id"):
                if not value or not value.strip():
                    raise ValueError(f"Parameter '{name}' cannot be empty")

    async def process_session_start(
        self,
        session_id: str,
        student_id: str,
        language: str,
        unit_number: int,
        exercise_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Procesa el inicio de una sesión de entrenamiento.

        Crea la secuencia de trazas N4 para la sesión si está habilitado.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            language: Lenguaje de programación
            unit_number: Número de unidad
            exercise_ids: IDs de los ejercicios en la sesión

        Returns:
            Diccionario con trace_sequence_id si se creó

        Raises:
            ValueError: If required parameters are invalid
        """
        # FIX Cortez68 (MEDIUM): Add input validation
        self._validate_input(
            session_id=session_id,
            student_id=student_id,
            language=language
        )

        result = {
            "trace_sequence_id": None,
            "features_enabled": []
        }

        if not self.config.enable_n4_tracing:
            return result

        if not self.trace_collector:
            logger.warning("N4 tracing enabled but no trace_collector configured")
            return result

        try:
            sequence = await asyncio.wait_for(
                self.trace_collector.create_session_sequence(
                    session_id=session_id,
                    student_id=student_id,
                    activity_type="training",
                    metadata={
                        "language": language,
                        "unit_number": unit_number,
                        "exercise_ids": exercise_ids
                    }
                ),
                timeout=self.config.trace_capture_timeout
            )

            result["trace_sequence_id"] = sequence.id if sequence else None
            result["features_enabled"].append("n4_tracing")

            logger.info(
                "Created trace sequence for training session",
                extra={
                    "session_id": session_id,
                    "sequence_id": result["trace_sequence_id"]
                }
            )

        except asyncio.TimeoutError:
            logger.warning(
                "Trace sequence creation timed out for session %s",
                session_id
            )
        except Exception as e:
            logger.error(
                "Failed to create trace sequence: %s: %s",
                type(e).__name__, e,
                exc_info=True
            )

        return result

    async def process_code_submission(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        sandbox_result: Dict[str, Any],
        attempt_number: int,
        previous_code: Optional[str] = None,
        time_since_last_seconds: Optional[float] = None,
        evaluation_result: Optional[Dict[str, Any]] = None
    ) -> CodeSubmissionResult:
        """
        Procesa un envío de código enriqueciendo con trazabilidad y análisis de riesgos.

        Este método NO ejecuta los tests ni evalúa el código; eso lo hace el
        CodeEvaluator existente. Este método agrega las capas de trazabilidad
        y análisis de riesgos.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            code: Código enviado
            sandbox_result: Resultado del sandbox (tests)
            attempt_number: Número de intento
            previous_code: Código del intento anterior (para diff)
            time_since_last_seconds: Segundos desde el último intento
            evaluation_result: Resultado de la evaluación (si ya se hizo)

        Returns:
            CodeSubmissionResult con trazas y alertas de riesgo
        """
        start_time = datetime.now()
        features_used = []

        result = CodeSubmissionResult(
            evaluation_result=evaluation_result or {}
        )

        # Crear tareas paralelas para trazabilidad y análisis de riesgos
        tasks = []

        # Tarea 1: Captura de traza N4
        if self.config.enable_n4_tracing and self.trace_collector:
            tasks.append(
                self._capture_submission_trace(
                    session_id=session_id,
                    student_id=student_id,
                    exercise_id=exercise_id,
                    code=code,
                    sandbox_result=sandbox_result,
                    attempt_number=attempt_number,
                    previous_code=previous_code
                )
            )
            features_used.append("n4_tracing")

        # Tarea 2: Análisis de riesgos
        if self.config.enable_risk_monitor and self.risk_monitor:
            tasks.append(
                self._analyze_submission_risks(
                    session_id=session_id,
                    student_id=student_id,
                    exercise_id=exercise_id,
                    code=code,
                    attempt_number=attempt_number,
                    time_since_last_seconds=time_since_last_seconds
                )
            )
            features_used.append("risk_monitor")

        # Ejecutar tareas en paralelo
        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Procesar resultados
                for i, task_result in enumerate(results):
                    if isinstance(task_result, Exception):
                        logger.error(
                            "Task %d failed: %s: %s",
                            i, type(task_result).__name__, task_result
                        )
                        continue

                    # Resultado de traza
                    if "trace_id" in task_result:
                        result.trace_id = task_result.get("trace_id")
                        result.cognitive_state_inferred = task_result.get("cognitive_state")
                        result.inference_confidence = task_result.get("confidence", 0.0)

                    # Resultado de riesgos
                    if "risk_flags" in task_result:
                        result.risk_flags = task_result.get("risk_flags", [])
                        result.risk_alerts = task_result.get("alerts", [])

            except Exception as e:
                logger.error(
                    "Error processing submission tasks: %s: %s",
                    type(e).__name__, e,
                    exc_info=True
                )

        # Calcular tiempo de procesamiento
        result.processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        result.features_used = features_used

        logger.info(
            "Processed code submission in %.2fms",
            result.processing_time_ms,
            extra={
                "session_id": session_id,
                "trace_id": result.trace_id,
                "risk_flags_count": len(result.risk_flags),
                "features_used": features_used
            }
        )

        return result

    async def _capture_submission_trace(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        sandbox_result: Dict[str, Any],
        attempt_number: int,
        previous_code: Optional[str]
    ) -> Dict[str, Any]:
        """Captura traza N4 de un envío de código."""
        try:
            trace_result = await asyncio.wait_for(
                self.trace_collector.trace_code_attempt(
                    session_id=session_id,
                    student_id=student_id,
                    exercise_id=exercise_id,
                    code=code,
                    result=sandbox_result,
                    attempt_number=attempt_number,
                    previous_code=previous_code
                ),
                timeout=self.config.trace_capture_timeout
            )

            return {
                "trace_id": trace_result.get("trace_id"),
                "cognitive_state": trace_result.get("cognitive_state_inferred"),
                "confidence": trace_result.get("inference_confidence", 0.0)
            }

        except asyncio.TimeoutError:
            logger.warning("Trace capture timed out for session %s", session_id)
            return {}
        except Exception as e:
            logger.error("Trace capture failed: %s: %s", type(e).__name__, e)
            return {}

    async def _analyze_submission_risks(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        code: str,
        attempt_number: int,
        time_since_last_seconds: Optional[float]
    ) -> Dict[str, Any]:
        """Analiza riesgos en un envío de código."""
        try:
            risk_result = await asyncio.wait_for(
                self.risk_monitor.analyze_attempt(
                    session_id=session_id,
                    student_id=student_id,
                    exercise_id=exercise_id,
                    code=code,
                    attempt_number=attempt_number,
                    time_since_last_seconds=time_since_last_seconds
                ),
                timeout=self.config.risk_analysis_timeout
            )

            return {
                "risk_flags": risk_result.get("flags", []),
                "alerts": risk_result.get("alerts", [])
            }

        except asyncio.TimeoutError:
            logger.warning("Risk analysis timed out for session %s", session_id)
            return {"risk_flags": [], "alerts": []}
        except Exception as e:
            logger.error("Risk analysis failed: %s: %s", type(e).__name__, e)
            return {"risk_flags": [], "alerts": []}

    async def process_hint_request(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        hint_number: int,
        exercise_data: Dict[str, Any],
        static_hints: List[str],
        attempt_history: Optional[List[Dict[str, Any]]] = None,
        last_error: Optional[str] = None
    ) -> HintRequestResult:
        """
        Procesa una solicitud de pista.

        Si está habilitado, usa T-IA-Cog para generar pistas contextuales.
        Si no, o si falla, usa las pistas estáticas de la base de datos.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            hint_number: Número de pista solicitada (0-based)
            exercise_data: Datos del ejercicio (titulo, consigna, etc.)
            static_hints: Pistas estáticas de la BD
            attempt_history: Historial de intentos del estudiante
            last_error: Último error del estudiante (si hay)

        Returns:
            HintRequestResult con el contenido de la pista
        """
        start_time = datetime.now()

        # Validar que hay pistas disponibles
        if not static_hints or hint_number >= len(static_hints):
            return HintRequestResult(
                hint_content="No hay más pistas disponibles para este ejercicio.",
                hint_number=hint_number,
                total_hints=len(static_hints) if static_hints else 0,
                source="error"
            )

        # Capturar traza de solicitud de pista (si habilitado)
        trace_id = None
        if self.config.enable_n4_tracing and self.trace_collector:
            try:
                trace = await self.trace_collector.trace_hint_request(
                    session_id=session_id,
                    student_id=student_id,
                    exercise_id=exercise_id,
                    hint_number=hint_number
                )
                trace_id = trace.get("trace_id") if trace else None
            except Exception as e:
                logger.warning("Failed to capture hint trace: %s", e)

        # Intentar generar pista contextual con T-IA-Cog
        if (self.config.use_tutor_hints and
            self.hints_strategy and
            self.llm_provider and
            attempt_history):  # Solo si hay historial de intentos

            try:
                contextual_hint = await asyncio.wait_for(
                    self.hints_strategy.generate_contextual_hint(
                        exercise_data=exercise_data,
                        hint_level=hint_number + 1,  # 1-based para la estrategia
                        attempt_history=attempt_history,
                        last_error=last_error,
                        llm_provider=self.llm_provider
                    ),
                    timeout=self.config.hint_generation_timeout
                )

                if contextual_hint and contextual_hint.get("content"):
                    generation_time = (datetime.now() - start_time).total_seconds() * 1000

                    logger.info(
                        "Generated contextual hint in %.2fms",
                        generation_time,
                        extra={
                            "session_id": session_id,
                            "exercise_id": exercise_id,
                            "hint_number": hint_number
                        }
                    )

                    return HintRequestResult(
                        hint_content=contextual_hint["content"],
                        hint_number=hint_number,
                        total_hints=len(static_hints),
                        trace_id=trace_id,
                        source="tutor_ai",
                        generation_time_ms=generation_time,
                        help_level=contextual_hint.get("help_level")
                    )

            except asyncio.TimeoutError:
                logger.warning(
                    "Contextual hint generation timed out, falling back to static",
                    extra={"session_id": session_id}
                )
            except Exception as e:
                logger.warning(
                    "Contextual hint generation failed, falling back to static: %s",
                    e,
                    extra={"session_id": session_id}
                )

        # Fallback: usar pista estática
        generation_time = (datetime.now() - start_time).total_seconds() * 1000

        return HintRequestResult(
            hint_content=static_hints[hint_number],
            hint_number=hint_number,
            total_hints=len(static_hints),
            trace_id=trace_id,
            source="static",
            generation_time_ms=generation_time
        )

    async def process_reflection(
        self,
        session_id: str,
        student_id: str,
        exercise_id: str,
        what_was_difficult: str,
        how_solved: str,
        what_learned: str,
        alternatives_considered: Optional[List[str]] = None,
        errors_made: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Procesa una reflexión post-ejercicio.

        Captura una traza N4 de tipo REFLECTION con las justificaciones
        explícitas del estudiante.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante
            exercise_id: ID del ejercicio
            what_was_difficult: Respuesta a "¿Qué fue lo más difícil?"
            how_solved: Respuesta a "¿Cómo lo resolviste?"
            what_learned: Respuesta a "¿Qué aprendiste?"
            alternatives_considered: Alternativas que consideró (opcional)
            errors_made: Errores que reconoce haber cometido (opcional)

        Returns:
            Diccionario con trace_id y xp_earned
        """
        result = {
            "trace_id": None,
            "xp_earned": 0,
            "success": False
        }

        if not self.config.enable_n4_tracing or not self.trace_collector:
            # Aunque no se capture traza, se puede dar XP
            result["xp_earned"] = 20  # XP base por reflexionar
            result["success"] = True
            return result

        try:
            trace = await self.trace_collector.trace_reflection(
                session_id=session_id,
                student_id=student_id,
                exercise_id=exercise_id,
                content=how_solved,
                decision_justification=what_learned,
                alternatives_considered=alternatives_considered or [],
                context={
                    "difficulty_reported": what_was_difficult,
                    "errors_acknowledged": errors_made or []
                }
            )

            result["trace_id"] = trace.get("trace_id") if trace else None
            result["xp_earned"] = 20  # XP por reflexión
            result["success"] = True

            logger.info(
                "Captured reflection trace",
                extra={
                    "session_id": session_id,
                    "exercise_id": exercise_id,
                    "trace_id": result["trace_id"]
                }
            )

        except Exception as e:
            logger.error(
                "Failed to capture reflection trace: %s: %s",
                type(e).__name__, e
            )
            # Aún así damos XP, la reflexión se hizo
            result["xp_earned"] = 20
            result["success"] = True

        return result

    async def get_session_process_analysis(
        self,
        session_id: str,
        student_id: str
    ) -> Dict[str, Any]:
        """
        Obtiene análisis del proceso de resolución de una sesión.

        Reconstruye el camino cognitivo y calcula métricas de proceso.

        Args:
            session_id: ID de la sesión
            student_id: ID del estudiante

        Returns:
            Diccionario con análisis de proceso
        """
        if not self.trace_collector:
            return {
                "error": "Traceability not configured",
                "traces": [],
                "metrics": {}
            }

        try:
            analysis = await self.trace_collector.get_process_analysis(
                session_id=session_id,
                student_id=student_id
            )

            return analysis

        except Exception as e:
            logger.error(
                "Failed to get process analysis: %s: %s",
                type(e).__name__, e
            )
            return {
                "error": str(e),
                "traces": [],
                "metrics": {}
            }


def create_training_gateway_from_config() -> TrainingGateway:
    """
    Factory function para crear TrainingGateway desde configuración.

    Lee los feature flags de variables de entorno.
    """
    import os

    config = TrainingGatewayConfig(
        use_tutor_hints=os.getenv("TRAINING_USE_TUTOR_HINTS", "false").lower() == "true",
        enable_n4_tracing=os.getenv("TRAINING_N4_TRACING", "false").lower() == "true",
        enable_risk_monitor=os.getenv("TRAINING_RISK_MONITOR", "false").lower() == "true",
    )

    # Los componentes se inyectan después según lo que esté habilitado
    return TrainingGateway(config=config)
