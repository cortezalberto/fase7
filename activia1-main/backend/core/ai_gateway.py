"""
AI Gateway - Componente central que coordina todos los submodelos
Implementa la arquitectura C4 del ecosistema AI-Native

REFACTORIZADO (2025-11-19):
- Ahora es completamente STATELESS (no mantiene estado en memoria)
- Dependency Injection completa (repositorios inyectados)
- Escalable (puede funcionar con múltiples instancias)
- Testeable (fácil mockear dependencias)
- Cache LLM integrado (opcional, reduce costos 30-50%)

FUTURE ENHANCEMENT (REC-MED-6 - Audit Cortez):
Background Tasks for Risk Analysis:
- Currently risk analysis runs synchronously in _analyze_risks_async()
- For better UX and scalability, consider implementing:
  1. FastAPI BackgroundTasks for simple async processing
  2. Celery + Redis for distributed task queue
  3. WebSocket notifications when analysis completes
- This would allow immediate response to user while analysis runs in background
- See: https://fastapi.tiangolo.com/tutorial/background-tasks/
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import logging
import time
import asyncio

from .cognitive_engine import CognitiveReasoningEngine, AgentMode
from ..models.trace import CognitiveTrace, TraceLevel, InteractionType, TraceSequence
from ..models.risk import Risk, RiskType, RiskLevel, RiskDimension, RiskReport
from ..models.evaluation import EvaluationReport
from ..llm import LLMProviderFactory, LLMProvider, LLMMessage, LLMRole
from .cache import LLMResponseCache
from ..agents.governance import GobernanzaAgent
# FIX Cortez68 (HIGH-005): Import protocols from gateway module instead of duplicating
from .gateway.protocols import (
    SessionRepositoryProtocol,
    TraceRepositoryProtocol,
    RiskRepositoryProtocol,
    EvaluationRepositoryProtocol,
    SequenceRepositoryProtocol,
)

# Prometheus metrics instrumentation (HIGH-01)
# Lazy import to avoid circular dependency with api.monitoring
# FIXED: Added thread safety with double-checked locking pattern
import threading

_metrics_module = None
_metrics_lock = threading.Lock()

def _get_metrics():
    """
    Lazy load metrics module to avoid circular imports.

    Thread-safe implementation using double-checked locking pattern.
    This prevents race conditions when multiple threads try to initialize
    the metrics module simultaneously.
    """
    global _metrics_module
    if _metrics_module is None:
        with _metrics_lock:
            # Double-check inside lock to avoid race condition
            if _metrics_module is None:
                try:
                    from ..api.monitoring import metrics as m
                    _metrics_module = m
                except ImportError:
                    _metrics_module = False  # Mark as unavailable
    return _metrics_module if _metrics_module else None

logger = logging.getLogger(__name__)


# FIX Cortez68 (HIGH-005): Protocol definitions removed - now imported from gateway.protocols
# See: backend/core/gateway/protocols.py for canonical definitions


class AIGateway:
    """
    AI Gateway - Orquestador central STATELESS del ecosistema AI-Native

    Componentes:
    - C1: Motor LLM (conexión a OpenAI/Anthropic/etc)
    - C2: Ingesta y Comprensión de Prompt (IPC)
    - C3: Motor de Razonamiento Cognitivo-Pedagógico (CRPE)
    - C4: Gobernanza, Seguridad y Riesgo (GSR)
    - C5: Orquestación de Submodelos (OSM)
    - C6: Trazabilidad Cognitiva N4

    Integra:
    - T-IA-Cog: Tutor IA Cognitivo
    - E-IA-Proc: Evaluador de Procesos
    - S-IA-X: Simuladores Profesionales
    - AR-IA: Analista de Riesgo
    - GOV-IA: Gobernanza
    - TC-N4: Trazabilidad

    IMPORTANTE: Gateway es STATELESS
    - Todo el estado se persiste en BD via repositorios
    - No mantiene sesiones/trazas/riesgos en memoria
    - Puede usarse con múltiples instancias (load balancer)
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        cognitive_engine: Optional[CognitiveReasoningEngine] = None,
        session_repo: Optional[SessionRepositoryProtocol] = None,
        trace_repo: Optional[TraceRepositoryProtocol] = None,
        risk_repo: Optional[RiskRepositoryProtocol] = None,
        evaluation_repo: Optional[EvaluationRepositoryProtocol] = None,
        sequence_repo: Optional[SequenceRepositoryProtocol] = None,
        cache: Optional[LLMResponseCache] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa el AI Gateway con Dependency Injection completa

        Args:
            llm_provider: Proveedor de LLM (inyectado)
            cognitive_engine: Motor de razonamiento cognitivo (inyectado)
            session_repo: Repositorio de sesiones (inyectado)
            trace_repo: Repositorio de trazas (inyectado)
            risk_repo: Repositorio de riesgos (inyectado)
            evaluation_repo: Repositorio de evaluaciones (inyectado)
            sequence_repo: Repositorio de secuencias (inyectado)
            cache: Cache de respuestas LLM (inyectado, opcional)
            config: Configuración adicional

        Note:
            Si no se inyectan dependencias, se crean con valores por defecto
            (útil para backward compatibility con código existente)
        """
        self.config = config or {}

        # C1: Motor LLM - Usar proveedor inyectado o crear uno por defecto
        if llm_provider is not None:
            self.llm = llm_provider
        else:
            # Backward compatibility: crear proveedor mock por defecto
            self.llm = LLMProviderFactory.create("mock", self.config.get("llm", {}))

        # C3: Motor de Razonamiento Cognitivo-Pedagógico - Inyectado
        if cognitive_engine is not None:
            self.cognitive_engine = cognitive_engine
        else:
            # Backward compatibility
            self.cognitive_engine = CognitiveReasoningEngine(self.config)
        
        # C4: Agente de Gobernanza - Instanciar para filtrado PII
        self.governance_agent = GobernanzaAgent(llm_provider=None, config=self.config)

        # Repositorios inyectados (opcional para backward compatibility)
        self.session_repo = session_repo
        self.trace_repo = trace_repo
        self.risk_repo = risk_repo
        self.evaluation_repo = evaluation_repo
        self.sequence_repo = sequence_repo

        # Cache LLM (opcional, para reducir costos)
        self.cache = cache

        # FIX Cortez35: Task registry to prevent garbage collection of background tasks
        # This keeps a strong reference to running tasks so they don't get GC'd
        self._background_tasks: set = set()

        # ✅ ELIMINADO: No más estado en memoria
        # ❌ self.trace_sequences: Dict[str, TraceSequence] = {}
        # ❌ self.traces: List[CognitiveTrace] = []
        # ❌ self.risks: Dict[str, RiskReport] = {}
        # ❌ self.active_sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        student_id: str,
        activity_id: str,
        mode: str = "TUTOR",
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Crea una nueva sesión de interacción (STATELESS)

        Args:
            student_id: ID del estudiante
            activity_id: ID de la actividad
            mode: Modo del agente (TUTOR, EVALUATOR, etc.)
            session_id: ID de sesión (opcional, se genera si no se proporciona)
            metadata: Metadata adicional

        Returns:
            session_id: ID de la sesión creada

        Note:
            Si session_repo está inyectado, persiste en BD.
            Si no, solo retorna el ID (backward compatibility para CLI).
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # ✅ STATELESS: Persistir en BD via repositorio (si está inyectado)
        if self.session_repo is not None:
            db_session = self.session_repo.create(
                student_id=student_id,
                activity_id=activity_id,
                mode=mode
            )
            session_id = db_session.id

        # ✅ STATELESS: Crear secuencia de trazas en BD (si está inyectado)
        if self.sequence_repo is not None:
            trace_sequence = TraceSequence(
                id=f"seq_{session_id}",
                session_id=session_id,
                student_id=student_id,
                activity_id=activity_id
            )
            self.sequence_repo.create(trace_sequence)

        # ❌ ELIMINADO: No más guardado en memoria
        # self.active_sessions[session_id] = session
        # self.trace_sequences[session_id] = trace_sequence

        return session_id

    async def process_interaction(
        self,
        session_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        flow_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Procesa una interacción del estudiante a través del gateway (STATELESS)

        Este es el flujo principal que:
        1. Valida entrada
        2. Obtiene sesión desde BD (no de memoria)
        3. Clasifica el prompt (IPC)
        4. Verifica gobernanza (GSR)
        5. Genera estrategia pedagógica (CRPE)
        6. Detecta riesgos (AR-IA)
        7. Registra en trazabilidad (N4) vía repositorio
        8. Genera respuesta según el agente activo

        Args:
            session_id: ID de la sesión
            prompt: Prompt del estudiante
            context: Contexto adicional

        Returns:
            Diccionario con la respuesta y metadata

        Raises:
            ValueError: Si la entrada no cumple con los requisitos de validación
        """
        flow_id = flow_id or f"flow_{uuid.uuid4()}"
        flow_started_at = time.perf_counter()
        logger.info(
            "Interaction flow started",
            extra={
                "flow_id": flow_id,
                "session_id": session_id,
                "prompt_preview": prompt[:160],
                "context_keys": sorted((context or {}).keys()) if context else [],
                # FIX Cortez68 (MEDIUM): Use timezone-aware datetime
                "timestamp": datetime.now(tz=__import__('datetime').timezone.utc).isoformat()
            }
        )

        # ✅ VALIDACIÓN: Validar entrada antes de procesar
        self._validate_interaction_input(session_id, prompt, context)

        # ✅ GOBERNANZA: Filtrar PII del prompt antes de procesarlo
        sanitized_prompt, pii_detected = self.governance_agent.sanitize_prompt(prompt)
        if pii_detected:
            logger.warning(
                "PII detectado y removido del prompt",
                extra={
                    "session_id": session_id,
                    "original_length": len(prompt),
                    "flow_id": flow_id
                }
            )
            prompt = sanitized_prompt
            logger.info(
                "Prompt sanitized after PII detection",
                extra={
                    "flow_id": flow_id,
                    "session_id": session_id,
                    "pii_detected": True,
                    "sanitized_length": len(prompt)
                }
            )

        # ✅ STATELESS: Obtener sesión desde BD (no desde self.active_sessions)
        # TODO Cortez68 (CRIT-006): Consider adding optimistic locking with version field
        # to prevent race conditions on concurrent session modifications. This requires
        # adding a `version` column to SessionDB and incrementing it on each update.
        if self.session_repo is not None:
            db_session = self.session_repo.get_by_id(session_id)
            if not db_session:
                raise ValueError(f"Sesión {session_id} no encontrada en BD")

            student_id = db_session.student_id
            activity_id = db_session.activity_id
            current_mode = AgentMode(db_session.mode.upper())
            logger.info(
                "Session context loaded",
                extra={
                    "flow_id": flow_id,
                    "session_id": session_id,
                    "student_id": student_id,
                    "activity_id": activity_id,
                    "agent_mode": current_mode.value
                }
            )
        else:
            raise ValueError("Session repo no disponible - no se puede procesar interacción")

        # C2: Ingesta y Comprensión de Prompt (IPC)
        classification = self.cognitive_engine.classify_prompt(
            prompt,
            context or {}
        )
        logger.info(
            "Prompt classified",
            extra={
                "session_id": session_id,
                "student_id": student_id,
                "classification": classification,
                "flow_id": flow_id
            }
        )

        # C4: Gobernanza - verificar si debe bloquearse
        should_block, block_reason = self.cognitive_engine.should_block_response(classification)
        logger.info(
            "Governance decision evaluated",
            extra={
                "flow_id": flow_id,
                "session_id": session_id,
                "should_block": should_block,
                "block_reason": block_reason
            }
        )

        # C6: Registrar traza de entrada (N3/N4)
        input_trace = self._create_trace(
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=prompt,
            level=TraceLevel.N4_COGNITIVO,
            cognitive_intent=classification.get("cognitive_state", "").value if classification.get("cognitive_state") else None,
            context={"classification": classification}
        )
        self._persist_trace(input_trace)

        # Si debe bloquearse, retornar mensaje pedagógico
        if should_block:
            response = self._generate_blocked_response(block_reason, classification)

            # Registrar la intervención
            intervention_trace = self._create_trace(
                session_id=session_id,
                student_id=student_id,
                activity_id=activity_id,
                interaction_type=InteractionType.TUTOR_INTERVENTION,
                content=response.get("response", response.get("message", "")),  # Support both keys
                level=TraceLevel.N4_COGNITIVO,
                agent_id="GOV-IA"
            )
            self._persist_trace(intervention_trace)

            # Registrar riesgo detectado
            self._persist_risk(
                session_id=session_id,
                student_id=student_id,
                activity_id=activity_id,
                risk_type=RiskType.COGNITIVE_DELEGATION,
                risk_level=RiskLevel.HIGH,
                dimension=RiskDimension.COGNITIVE,
                description="Delegación total detectada en el prompt",
                evidence=[prompt],
                trace_ids=[input_trace.id],
                flow_id=flow_id
            )

            # ✅ HIGH-01: Record Prometheus metrics for governance block
            metrics = _get_metrics()
            if metrics:
                metrics.record_interaction(
                    session_id=session_id,
                    student_id=student_id,
                    agent_used="GOV-IA",
                    status="blocked"
                )
                metrics.record_governance_block(
                    reason="total_delegation",
                    session_id=session_id
                )

            logger.info(
                "Interaction flow completed",
                extra={
                    "flow_id": flow_id,
                    "session_id": session_id,
                    "agent_mode": current_mode.value,
                    "outcome": "blocked",
                    "duration_ms": round((time.perf_counter() - flow_started_at) * 1000, 2)
                }
            )
            return response

        # C3: Generar estrategia pedagógica
        student_history = self._get_student_history(student_id, activity_id)
        strategy = self.cognitive_engine.generate_pedagogical_response_strategy(
            prompt,
            classification,
            student_history
        )
        # Log strategy generation
        logger.info(
            "Pedagogical strategy generated",
            extra={
                "session_id": session_id,
                "student_id": student_id,
                "strategy": strategy,
                "flow_id": flow_id
            }
        )

        # C5: Orquestación - delegar al submodelo apropiado
        logger.info(
            "Orchestrating to agent",
            extra={
                "session_id": session_id,
                "agent": current_mode.value,
                "prompt_preview": prompt[:200],
                "flow_id": flow_id
            }
        )

        agent_started_at = time.perf_counter()
        if current_mode == AgentMode.TUTOR:
            response = await self._process_tutor_mode(
                session_id, prompt, strategy, classification, flow_id=flow_id
            )
        elif current_mode == AgentMode.SIMULATOR:
            # FIX Cortez22 DEFECTO 1.1: Add await for async method
            response = await self._process_simulator_mode(
                session_id, prompt, strategy, classification, flow_id=flow_id
            )
        elif current_mode == AgentMode.EVALUATOR:
            # FIX Cortez22 DEFECTO 1.1: Add await for async method
            response = await self._process_evaluator_mode(
                session_id, prompt, strategy, classification, flow_id=flow_id
            )
        else:
            # FIX Cortez22 DEFECTO 1.8: Use "response" not "message"
            response = {"response": "Modo no implementado", "metadata": {}}
        agent_duration_ms = round((time.perf_counter() - agent_started_at) * 1000, 2)
        logger.info(
            "Agent response generated",
            extra={
                "flow_id": flow_id,
                "session_id": session_id,
                "agent_mode": current_mode.value,
                "from_cache": response.get("metadata", {}).get("from_cache"),
                "duration_ms": agent_duration_ms
            }
        )

        # Registrar respuesta en trazas
        response_trace = self._create_trace(
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            interaction_type=InteractionType.AI_RESPONSE,
            content=response.get("response", response.get("message", "")),  # Support both keys
            level=TraceLevel.N4_COGNITIVO,
            agent_id=current_mode.value,
            context={"strategy": strategy}
        )
        self._persist_trace(response_trace)

        # Análisis de riesgo en paralelo (AR-IA)
        self._run_risk_analysis_background(
            session_id,
            input_trace,
            response_trace,
            classification,
            flow_id
        )

        # ✅ HIGH-01: Record Prometheus metrics for successful interaction
        metrics = _get_metrics()
        if metrics:
            metrics.record_interaction(
                session_id=session_id,
                student_id=student_id,
                agent_used=current_mode.value,
                status="success"
            )
            # Record cognitive state if available
            cognitive_state = classification.get("cognitive_state")
            if cognitive_state:
                metrics.record_cognitive_state(cognitive_state.value if hasattr(cognitive_state, 'value') else str(cognitive_state))

        logger.info(
            "Interaction flow completed",
            extra={
                "flow_id": flow_id,
                "session_id": session_id,
                "agent_mode": current_mode.value,
                "outcome": "success",
                "duration_ms": round((time.perf_counter() - flow_started_at) * 1000, 2)
            }
        )
        return response

    def _run_risk_analysis_background(
        self,
        session_id: str,
        input_trace: CognitiveTrace,
        response_trace: CognitiveTrace,
        classification: Dict[str, Any],
        flow_id: Optional[str]
    ) -> None:
        """Ejecuta el análisis de riesgo en background para liberar la respuesta principal."""
        if self.risk_repo is None:
            # Sin repositorio no podemos persistir riesgos (compatibilidad/backward)
            self._analyze_risks_async(session_id, input_trace, response_trace, classification, flow_id)
            return

        logger.info(
            "Scheduling risk analysis task",
            extra={
                "flow_id": flow_id,
                "session_id": session_id,
                "input_trace_id": input_trace.id,
                "response_trace_id": response_trace.id
            }
        )

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Entorno síncrono (por ejemplo, tests) => ejecutar inline para conservar comportamiento
            self._analyze_risks_async(session_id, input_trace, response_trace, classification, flow_id)
            return

        def _analyze_with_fresh_db_session() -> None:
            """Run risk analysis using a brand-new DB session (safe for background threads)."""
            try:
                from ..database import get_db_session
                from ..database.repositories import RiskRepository
            except Exception:
                logger.error(
                    "Failed to import database helpers for background risk analysis",
                    exc_info=True,
                    extra={"flow_id": flow_id, "session_id": session_id}
                )
                return

            with get_db_session() as db_session:
                risk_repo = RiskRepository(db_session)
                self._analyze_risks_async(
                    session_id,
                    input_trace,
                    response_trace,
                    classification,
                    flow_id,
                    risk_repo_override=risk_repo,
                )

        async def _async_task():
            # FIX Cortez68 (CRIT-005): Add retry mechanism for failed risk analysis
            max_retries = 3
            retry_delay = 1.0  # seconds
            started_at = time.perf_counter()
            last_exception = None

            for attempt in range(max_retries):
                try:
                    await asyncio.to_thread(
                        _analyze_with_fresh_db_session
                    )
                    logger.info(
                        "Risk analysis completed asynchronously",
                        extra={
                            "flow_id": flow_id,
                            "session_id": session_id,
                            "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                            "attempt": attempt + 1
                        }
                    )
                    return  # Success, exit
                except Exception as exc:
                    last_exception = exc
                    if attempt < max_retries - 1:
                        logger.warning(
                            "Risk analysis task failed, retrying",
                            extra={
                                "flow_id": flow_id,
                                "session_id": session_id,
                                "attempt": attempt + 1,
                                "max_retries": max_retries,
                                "retry_delay": retry_delay
                            }
                        )
                        await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    else:
                        logger.error(
                            "Risk analysis task failed after all retries",
                            exc_info=True,
                            extra={
                                "flow_id": flow_id,
                                "session_id": session_id,
                                "input_trace_id": input_trace.id,
                                "response_trace_id": response_trace.id,
                                "total_attempts": max_retries,
                                "error": str(last_exception)
                            }
                        )

        # FIX Cortez34: Add done callback to track task completion and log errors
        # FIX Cortez35: Also remove task from registry when done
        def _task_done_callback(task: asyncio.Task) -> None:
            """Callback to log unhandled exceptions and cleanup task registry."""
            # FIX Cortez35: Remove from registry to allow GC after completion
            self._background_tasks.discard(task)

            try:
                exc = task.exception()
                if exc is not None:
                    logger.error(
                        "Background risk analysis task raised unhandled exception",
                        exc_info=exc,
                        extra={
                            "flow_id": flow_id,
                            "session_id": session_id,
                            "task_name": task.get_name()
                        }
                    )
            except asyncio.CancelledError:
                logger.warning(
                    "Background risk analysis task was cancelled",
                    extra={"flow_id": flow_id, "session_id": session_id}
                )
            except asyncio.InvalidStateError:
                pass  # Task not done yet, ignore

        task = loop.create_task(_async_task(), name=f"risk_analysis_{session_id}")
        # FIX Cortez35: Add to registry to prevent GC while running
        self._background_tasks.add(task)
        task.add_done_callback(_task_done_callback)

    def _generate_blocked_response(
        self,
        reason: str,
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Genera una respuesta pedagógica cuando se bloquea la solicitud"""
        cognitive_state = classification.get("cognitive_state")

        message = f"""
He detectado que tu solicitud implica una delegación total del problema a la IA.

{reason}

Para poder ayudarte efectivamente, necesito que:

1. **Expliques tu comprensión del problema**: ¿Qué te piden resolver?
2. **Descompongas el problema**: ¿Qué partes identificas?
3. **Compartas tu plan inicial**: ¿Cómo pensás abordarlo?
4. **Identifiques tus dudas específicas**: ¿Qué parte específica te genera dificultad?

Esto no es una limitación arbitraria: el objetivo es que desarrolles tu capacidad de razonamiento y resolución de problemas, que son competencias fundamentales.

¿Podés reformular tu consulta siguiendo estas pautas?
"""

        return {
            "response": message.strip(),  # Changed from "message" to "response"
            "blocked": True,
            "block_reason": reason,  # Changed from "reason" to "block_reason"
            "requires_reformulation": True,
            "metadata": {
                "classification": classification,
                "pedagogical_intent": "promote_autonomy"
            }
        }

    async def _process_tutor_mode(
        self,
        session_id: str,
        prompt: str,
        strategy: Dict[str, Any],
        classification: Dict[str, Any],
        flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa la interacción en modo T-IA-Cog (Tutor)

        En el MVP, genera respuestas basadas en la estrategia pedagógica.
        En producción, integraría con LLM real.

        Integración de cache:
        - Verifica cache antes de generar respuesta
        - Guarda respuesta en cache después de generarla
        - Ahorra costos de LLM (30-50% en prompts repetidos)
        """
        response_type = strategy.get("response_type", "unknown")
        
        logger.info(
            "Processing tutor mode",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "response_type": response_type,
                "strategy_keys": sorted(strategy.keys()) if isinstance(strategy, dict) else []
            }
        )

        # Preparar contexto para cache key
        cache_context = {
            "response_type": response_type,
            "cognitive_state": classification.get("cognitive_state", "").value if classification.get("cognitive_state") else None
        }

        # Intentar obtener respuesta del cache
        cached_response = None
        if self.cache is not None:
            cached_response = self.cache.get(
                prompt=prompt,
                context=cache_context,
                mode="TUTOR"
            )

        if cached_response is not None:
            # Cache HIT - usar respuesta cacheada
            logger.info(
                f"Using cached response for prompt (saved LLM call)",
                extra={
                    "session_id": session_id,
                    "response_type": response_type,
                    "prompt_preview": prompt[:50],
                    "flow_id": flow_id
                }
            )
            message = cached_response
        else:
            # Cache MISS - generar respuesta nueva
            if response_type == "socratic_questioning":
                message = await self._generate_socratic_response(prompt, strategy, session_id, flow_id=flow_id)
            elif response_type == "conceptual_explanation":
                message = await self._generate_conceptual_explanation(prompt, strategy, session_id, flow_id=flow_id)
            elif response_type == "guided_hints":
                message = await self._generate_guided_hints(prompt, strategy, session_id, flow_id=flow_id)
            # ============================================================
            # NUEVOS TIPOS DE RESPUESTA (FIX Cortez64)
            # ============================================================
            elif response_type == "empathetic_support":
                message = await self._generate_empathetic_support(prompt, strategy, session_id, flow_id=flow_id)
            elif response_type == "metacognitive_guidance":
                message = await self._generate_metacognitive_guidance(prompt, strategy, session_id, flow_id=flow_id)
            elif response_type == "example_based":
                message = await self._generate_example_based(prompt, strategy, session_id, flow_id=flow_id)
            elif response_type == "clarification_request":
                message = await self._generate_clarification_request(prompt, strategy, session_id, flow_id=flow_id)
            else:
                # Fallback: usar explicación conceptual para casos no clasificados
                logger.warning(
                    "Unknown response_type received, using conceptual_explanation",
                    extra={
                        "session_id": session_id,
                        "flow_id": flow_id,
                        "response_type": response_type
                    }
                )
                message = await self._generate_conceptual_explanation(prompt, strategy, session_id, flow_id=flow_id)

            # Guardar en cache para futuras solicitudes idénticas
            if self.cache is not None:
                self.cache.set(
                    prompt=prompt,
                    response=message,
                    context=cache_context,
                    mode="TUTOR"
                )

        return {
            "response": message,  # Changed from "message" to "response"
            "strategy": strategy,
            "mode": "tutor",
            "metadata": {
                "response_type": response_type,
                "cognitive_state": classification.get("cognitive_state", "").value if classification.get("cognitive_state") else None,
                "from_cache": cached_response is not None
            }
        }

    async def _generate_socratic_response(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """✅ Genera respuesta socrática con memoria de conversación"""
        # Recuperar historial de conversación si hay session_id
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)
        
        # Construir mensajes con historial + system prompt + prompt actual
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor socrático. Tu objetivo es guiar al estudiante a descubrir la respuesta por sí mismo mediante preguntas orientadoras.

⚠️ REGLAS ESTRICTAS - NUNCA VIOLAR:
1. **PROHIBIDO ABSOLUTAMENTE dar código de programación** (ni completo, ni fragmentos, ni pseudocódigo detallado)
2. **NO des soluciones directas** - Solo haz preguntas que guíen el razonamiento
3. **NO escribas sintaxis de ningún lenguaje** - Solo conceptos y estrategias de alto nivel

Lo que SÍ puedes hacer:
- Hacer preguntas que exploren su comprensión actual
- Identificar sus suposiciones y ayudarlo a cuestionarlas
- Guiarlo a descomponer el problema conceptualmente
- Sugerir qué conceptos teóricos revisar
- Ayudarlo a encontrar la solución por sí mismo mediante razonamiento

Si te piden código directamente, RECHAZA cortésmente y redirige con preguntas:
- "En vez de darte el código, ayúdame a entender: ¿qué intentaste hasta ahora?"
- "¿Qué conceptos crees que necesitas aplicar para resolver esto?"
- "Explícame tu plan en lenguaje natural antes de codificar"

Sé breve y preciso. Máximo 4-5 preguntas por respuesta."""
            )
        ]
        
        # Agregar historial de conversación
        messages.extend(conversation_history)
        
        # Agregar prompt actual
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Pregunta: {prompt}"
            )
        )
        
        try:
            # Log messages sent to LLM (preview)
            logger.info(
                "Sending messages to LLM (socratic)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "messages_preview": [m.content[:200] for m in messages],
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # Decisión inteligente de modelo (híbrido: keywords + Flash decide)
            model_decision = await self._decide_model_for_prompt(prompt)
            use_pro = (model_decision == "pro")
            
            # Use Flash model for conversational tutoring (unless Pro is needed)
            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=300,
                    temperature=0.7,
                    is_code_analysis=use_pro  # Pro si Flash decidió que es necesario
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            # Log LLM response metadata and preview
            try:
                usage = response.usage if hasattr(response, 'usage') else None
                logger.info(
                    "LLM response received (socratic)",
                    extra={
                        "session_id": session_id,
                        "model": getattr(response, 'model', None),
                        "usage": usage,
                        "response_preview": response.content[:300],
                        "flow_id": flow_id,
                        "duration_ms": llm_duration_ms
                    }
                )
            except Exception:
                logger.debug("Could not log full LLM response metadata", exc_info=True)

            return response.content.strip()
        except Exception as e:
            # FIX Cortez36: Use lazy logging formatting
            logger.error("LLM generation failed: %s", e, exc_info=True)
            # Circuit Breaker: Fallback cuando Ollama está inaccesible
            return self._get_fallback_socratic_response(prompt, flow_id=flow_id)

    async def _decide_model_for_prompt(self, prompt: str) -> str:
        """
        Decide inteligentemente qué modelo usar (Flash o Pro)
        
        Enfoque híbrido:
        1. Primero: Check rápido con keywords (instantáneo)
        2. Si es obvio que necesita Pro -> usar Pro
        3. Si es obvio que NO necesita Pro -> usar Flash
        4. Si es ambiguo -> preguntarle a Flash que decida
        
        Args:
            prompt: La consulta del usuario
            
        Returns:
            "pro" o "flash" (nombre del modelo a usar)
        """
        # Keywords obvios que requieren Pro (análisis profundo)
        PRO_KEYWORDS = [
            'complejidad', 'complexity', 'big o', 'algoritmo complejo',
            'optimizar algoritmo', 'optimize algorithm', 'refactor',
            'arquitectura', 'architecture', 'diseño de sistema',
            'patrones de diseño', 'design patterns', 'solid principles',
            'analizar código', 'analyze code', 'revisar implementación',
            'debugging avanzado', 'advanced debug'
        ]
        
        # Keywords obvios que NO requieren Pro (conversación simple)
        FLASH_KEYWORDS = [
            '¿qué es', 'what is', 'explícame', 'explain',
            'hola', 'hello', 'ayuda', 'help',
            'gracias', 'thanks', 'entiendo', 'understand'
        ]
        
        prompt_lower = prompt.lower()
        
        # 1. Check rápido: ¿Obviamente necesita Pro?
        if any(keyword in prompt_lower for keyword in PRO_KEYWORDS):
            # FIX Cortez36: Use lazy logging formatting
            logger.info("Quick decision: Using Pro (matched keyword)")
            return "pro"

        # 2. Check rápido: ¿Obviamente NO necesita Pro?
        if any(keyword in prompt_lower for keyword in FLASH_KEYWORDS):
            # FIX Cortez36: Use lazy logging formatting
            logger.info("Quick decision: Using Flash (matched simple keyword)")
            return "flash"
        
        # 3. Caso ambiguo: Preguntarle a Flash que analice
        # Solo si es Gemini provider (que soporta analyze_complexity)
        if hasattr(self.llm, 'analyze_complexity'):
            try:
                analysis = await self.llm.analyze_complexity(prompt)
                decision = "pro" if analysis["needs_pro"] else "flash"
                # FIX Cortez68 (HIGH-009): Convert f-string logging to lazy format
                logger.info(
                    "Smart decision by Flash: Using %s",
                    decision,
                    extra={
                        "reason": analysis["reason"],
                        "confidence": analysis["confidence"]
                    }
                )
                return decision
            except Exception as e:
                # FIX Cortez36: Use lazy logging formatting
                logger.warning("Flash analysis failed: %s, defaulting to Flash", e)
                return "flash"
        
        # 4. Fallback: usar Flash por defecto (más económico)
        logger.info("Default decision: Using Flash")
        return "flash"

    async def _generate_conceptual_explanation(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """✅ Genera explicación conceptual con memoria de conversación"""
        # Recuperar historial de conversación si hay session_id
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)
        
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor pedagógico. Explica conceptos fundamentales de manera clara y didáctica.

⚠️ REGLA CRÍTICA:
**NUNCA proporciones código de programación.** Solo explica conceptos, estrategias y razonamientos.

Estructura tu explicación:
1. Concepto clave (definición simple en lenguaje natural)
2. Principio fundamental (por qué es importante)
3. Ejemplo conceptual (SIN código, solo la idea)
4. Aplicación práctica (cómo pensar el problema, no cómo implementarlo)

Si te preguntan por código específico:
- Explica el CONCEPTO detrás de lo que necesitan
- Describe la ESTRATEGIA de alto nivel
- Sugiere QUÉ buscar en la documentación
- NO escribas sintaxis de ningún lenguaje

Usa markdown para formato. Sé claro y conciso (máximo 200 palabras)."""
            )
        ]
        
        # Agregar historial
        messages.extend(conversation_history)
        
        # Agregar prompt actual
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Pregunta: {prompt}"
            )
        )
        
        try:
            logger.info(
                "Sending messages to LLM (conceptual)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "messages_preview": [m.content[:200] for m in messages],
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # Decisión inteligente: keywords rápidos + Flash analiza si es ambiguo
            model_decision = await self._decide_model_for_prompt(prompt)
            use_pro = (model_decision == "pro")

            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=400,
                    temperature=0.7,
                    is_code_analysis=use_pro
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            try:
                usage = response.usage if hasattr(response, 'usage') else None
                logger.info(
                    "LLM response received (conceptual)",
                    extra={
                        "session_id": session_id,
                        "model": getattr(response, 'model', None),
                        "usage": usage,
                        "response_preview": response.content[:300],
                        "flow_id": flow_id,
                        "duration_ms": llm_duration_ms
                    }
                )
            except Exception:
                logger.debug("Could not log full LLM response metadata", exc_info=True)

            return response.content.strip()
        except Exception as e:
            # FIX Cortez36: Use lazy logging formatting
            logger.error("LLM generation failed: %s", e, exc_info=True)
            # Circuit Breaker: Fallback cuando Ollama está inaccesible
            return self._get_fallback_conceptual_explanation(prompt, flow_id=flow_id)

    async def _generate_guided_hints(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """✅ Genera pistas guiadas con memoria de conversación"""
        # Recuperar historial de conversación si hay session_id
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)
        
        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor que da pistas graduadas. NO des la solución completa ni código.

⚠️ PROHIBIDO ESTRICTAMENTE:
- Escribir código funcional (ni completo, ni parcial)
- Dar pseudocódigo detallado con sintaxis
- Proporcionar implementaciones directas

Proporciona 3-4 pistas CONCEPTUALES que:
1. Sugieran cómo descomponer el problema (en ideas, no en código)
2. Mencionen conceptos/estructuras relevantes (nombres, no sintaxis)
3. Indiquen casos a considerar (situaciones, no implementación)
4. Sugieran un próximo paso de RAZONAMIENTO (pensar, no codificar)

Ejemplo de pista BUENA:
✅ "Pensá en qué estructura de datos te permite acceso rápido por clave"

Ejemplo de pista MALA (NO hacer):
❌ "Usá un HashMap y hacé: map.put(key, value)"

Cada pista debe acercar al estudiante a la solución conceptual sin dársela directamente."""
            )
        ]
        
        # Agregar historial
        messages.extend(conversation_history)
        
        # Agregar prompt actual
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Pregunta: {prompt}"
            )
        )
        
        try:
            logger.info(
                "Sending messages to LLM (guided_hints)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "messages_preview": [m.content[:200] for m in messages],
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # Decisión inteligente de modelo
            model_decision = await self._decide_model_for_prompt(prompt)
            use_pro = (model_decision == "pro")

            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=350,
                    temperature=0.7,
                    is_code_analysis=use_pro
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            try:
                usage = response.usage if hasattr(response, 'usage') else None
                logger.info(
                    "LLM response received (guided_hints)",
                    extra={
                        "session_id": session_id,
                        "model": getattr(response, 'model', None),
                        "usage": usage,
                        "response_preview": response.content[:300],
                        "flow_id": flow_id,
                        "duration_ms": llm_duration_ms
                    }
                )
            except Exception:
                logger.debug("Could not log full LLM response metadata", exc_info=True)

            return response.content.strip()
        except Exception as e:
            # FIX Cortez36: Use lazy logging formatting
            logger.error("LLM generation failed: %s", e, exc_info=True)
            # Circuit Breaker: Fallback cuando Ollama está inaccesible
            return self._get_fallback_guided_hints(prompt, flow_id=flow_id)

    # ============================================================
    # NUEVOS MÉTODOS DE GENERACIÓN DE RESPUESTA (FIX Cortez64)
    # ============================================================

    async def _generate_empathetic_support(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """
        FIX Cortez64: Genera respuesta empática para estudiantes frustrados.

        Reconoce la frustración, normaliza la dificultad, y ofrece un enfoque
        fresco con pistas más directas para desbloquear.
        """
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor empático y comprensivo. El estudiante está frustrado o atascado.

🎯 TU OBJETIVO: Reconocer su frustración, normalizarla, y ayudarlo a desbloquear.

✅ LO QUE DEBES HACER:
1. **Reconocer la frustración** - "Entiendo que esto es frustrante..." / "Es normal sentirse trabado..."
2. **Normalizar la dificultad** - "Este es un problema que toma tiempo..." / "Todos nos trabamos con esto al principio..."
3. **Ofrecer perspectiva fresca** - Sugerir mirar el problema desde otro ángulo
4. **Dar pistas más directas** - Ser más específico de lo usual para ayudar a desbloquear
5. **Sugerir pasos pequeños** - Dividir en partes manejables
6. **Mantener tono alentador** - "Ya avanzaste en X, ahora veamos Y..."

⚠️ PROHIBIDO:
- Dar código completo (pero sí puedes ser más específico con conceptos)
- Minimizar su frustración ("es fácil", "no es para tanto")
- Dar la solución directa

💡 Puedes ser más generoso con las pistas que en modo normal,
pero sin dar la solución completa.

Sé cálido, paciente y constructivo. Máximo 200 palabras."""
            )
        ]

        messages.extend(conversation_history)
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Estudiante frustrado dice: {prompt}"
            )
        )

        try:
            logger.info(
                "Sending messages to LLM (empathetic_support)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=400,
                    temperature=0.8  # Un poco más de variedad para empatía
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            logger.info(
                "LLM response received (empathetic_support)",
                extra={
                    "session_id": session_id,
                    "flow_id": flow_id,
                    "duration_ms": llm_duration_ms
                }
            )

            return response.content.strip()
        except Exception as e:
            logger.error("LLM generation failed (empathetic_support): %s", e, exc_info=True)
            return self._get_fallback_empathetic_support(prompt, flow_id=flow_id)

    async def _generate_metacognitive_guidance(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """
        FIX Cortez64: Genera guía metacognitiva para estudiantes que preguntan
        sobre cómo pensar o encarar un problema.
        """
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor especializado en metacognición y estrategias de aprendizaje.
El estudiante pregunta sobre CÓMO PENSAR o CÓMO ENCARAR un problema.

🎯 TU OBJETIVO: Enseñar el PROCESO de pensamiento, no el contenido.

✅ LO QUE DEBES HACER:
1. **Estrategia de descomposición** - "Primero, identifiquemos qué sabemos y qué nos piden..."
2. **Plan de acción** - "Un buen enfoque sería: 1) entender el input, 2) definir el output..."
3. **Técnicas de resolución** - Mencionar patrones como "dividir y conquistar", "casos base"
4. **Preguntas de autoevaluación** - "Preguntate: ¿qué pasa si el input está vacío?"
5. **Orden de pasos** - Dar una secuencia lógica para abordar problemas similares

⚠️ PROHIBIDO:
- Dar código o pseudocódigo detallado
- Resolver el problema específico directamente

💡 Enseñale a PESCAR, no le des el pescado.

Estructura tu respuesta como un plan de acción numerado.
Máximo 250 palabras."""
            )
        ]

        messages.extend(conversation_history)
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Estudiante pregunta sobre estrategia: {prompt}"
            )
        )

        try:
            logger.info(
                "Sending messages to LLM (metacognitive_guidance)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=450,
                    temperature=0.6  # Más estructurado
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            logger.info(
                "LLM response received (metacognitive_guidance)",
                extra={
                    "session_id": session_id,
                    "flow_id": flow_id,
                    "duration_ms": llm_duration_ms
                }
            )

            return response.content.strip()
        except Exception as e:
            logger.error("LLM generation failed (metacognitive_guidance): %s", e, exc_info=True)
            return self._get_fallback_metacognitive_guidance(prompt, flow_id=flow_id)

    async def _generate_example_based(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """
        FIX Cortez64: Genera respuesta basada en ejemplos análogos.

        Proporciona un ejemplo similar pero diferente al problema actual,
        guiando la transferencia del conocimiento.
        """
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor que enseña mediante ejemplos análogos.
El estudiante pidió un ejemplo para entender mejor.

🎯 TU OBJETIVO: Dar un ejemplo SIMILAR pero NO IDÉNTICO al problema.

✅ LO QUE DEBES HACER:
1. **Ejemplo análogo** - Usar un caso diferente pero con la misma estructura
   - Si pregunta sobre ordenar números, dar ejemplo de ordenar palabras alfabéticamente
   - Si pregunta sobre listas, dar ejemplo con otra colección

2. **Explicar el ejemplo** - Paso a paso, conceptualmente
3. **Preguntas de transferencia** - "¿Ves cómo esto se aplica a tu problema?"
4. **Conexión explícita** - Ayudar a ver el paralelo con su problema

⚠️ PROHIBIDO:
- Dar la solución directa a SU problema
- Dar código copiable para su ejercicio específico

💡 El ejemplo debe iluminar el PATRÓN, no resolver el problema.

Ejemplo de estructura:
"Imaginá que en lugar de [su problema] tenés [problema análogo]...
En ese caso, pensarías en... [explicación]
Ahora, ¿cómo aplicarías esta misma idea a tu problema?"

Máximo 300 palabras."""
            )
        ]

        messages.extend(conversation_history)
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Estudiante pide ejemplo: {prompt}"
            )
        )

        try:
            logger.info(
                "Sending messages to LLM (example_based)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "flow_id": flow_id
                }
            )

            llm_started_at = time.perf_counter()
            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=500,
                    temperature=0.7
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )
            llm_duration_ms = round((time.perf_counter() - llm_started_at) * 1000, 2)

            logger.info(
                "LLM response received (example_based)",
                extra={
                    "session_id": session_id,
                    "flow_id": flow_id,
                    "duration_ms": llm_duration_ms
                }
            )

            return response.content.strip()
        except Exception as e:
            logger.error("LLM generation failed (example_based): %s", e, exc_info=True)
            return self._get_fallback_example_based(prompt, flow_id=flow_id)

    async def _generate_clarification_request(
        self,
        prompt: str,
        strategy: Dict[str, Any],
        session_id: str = None,
        flow_id: Optional[str] = None
    ) -> str:
        """
        FIX Cortez64: Solicita clarificación cuando el prompt es ambiguo.
        Actualizado a async con LLM para respuestas más naturales.
        """
        conversation_history = []
        if session_id and self.trace_repo:
            conversation_history = self._load_conversation_history(session_id)

        messages = [
            LLMMessage(
                role=LLMRole.SYSTEM,
                content="""Eres un tutor que necesita más información para ayudar.
El mensaje del estudiante es ambiguo o le falta contexto.

🎯 TU OBJETIVO: Pedir clarificación de manera amable y específica.

✅ LO QUE DEBES HACER:
1. Reconocer que querés ayudar
2. Explicar qué información te falta
3. Hacer preguntas específicas:
   - ¿Qué parte exacta no entendés?
   - ¿Qué intentaste hasta ahora?
   - ¿Podés mostrar tu código actual?
   - ¿Qué resultado esperabas vs. qué obtuviste?

Sé amable y específico. Máximo 100 palabras."""
            )
        ]

        messages.extend(conversation_history)
        messages.append(
            LLMMessage(
                role=LLMRole.USER,
                content=f"Mensaje ambiguo: {prompt}"
            )
        )

        try:
            logger.info(
                "Sending messages to LLM (clarification_request)",
                extra={
                    "session_id": session_id,
                    "messages_count": len(messages),
                    "flow_id": flow_id
                }
            )

            # FIX Cortez68 (HIGH-004): Add timeout to prevent indefinite hangs
            LLM_TIMEOUT_SECONDS = 30.0
            response = await asyncio.wait_for(
                self.llm.generate(
                    messages,
                    max_tokens=200,
                    temperature=0.5
                ),
                timeout=LLM_TIMEOUT_SECONDS
            )

            return response.content.strip()
        except Exception as e:
            logger.error("LLM generation failed (clarification_request): %s", e, exc_info=True)
            return self._get_fallback_clarification_request(prompt, flow_id=flow_id)

    # ============================================================
    # FALLBACKS PARA NUEVOS TIPOS (FIX Cortez64)
    # ============================================================

    def _get_fallback_empathetic_support(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """Fallback para respuesta empática cuando LLM no está disponible."""
        return """Entiendo que te sentís frustrado/a, y es completamente normal.
Todos nos trabamos en algún momento cuando aprendemos a programar.

Tomemos un respiro y miremos esto desde otro ángulo:

1. **¿Qué parte SÍ entendés del problema?** Empezá por ahí.
2. **¿Podés dividirlo en partes más pequeñas?** A veces ayuda resolver pedacitos.
3. **¿Qué fue lo último que funcionó?** Volvamos a ese punto.

No te rindas. Cada error es un paso hacia la solución.
¿Por dónde te gustaría empezar de nuevo?"""

    def _get_fallback_metacognitive_guidance(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """Fallback para guía metacognitiva cuando LLM no está disponible."""
        return """Para encarar este tipo de problemas, te sugiero seguir estos pasos:

**Plan de Acción:**

1. **Entender el problema**
   - ¿Qué datos de entrada tenés?
   - ¿Qué resultado necesitás obtener?

2. **Identificar lo que sabés**
   - ¿Qué conceptos ya conocés que podrían servir?
   - ¿Resolviste algo similar antes?

3. **Descomponer en pasos**
   - ¿Cuál sería el primer paso más pequeño?
   - ¿Qué necesitás resolver primero?

4. **Probar con ejemplos simples**
   - ¿Qué pasaría con un caso muy sencillo?
   - ¿Y con un caso borde (vacío, un solo elemento)?

¿Podés empezar describiendo qué entendés del problema en tus palabras?"""

    def _get_fallback_example_based(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """Fallback para respuesta basada en ejemplos cuando LLM no está disponible."""
        return """Te doy un ejemplo análogo para que veas el patrón:

**Problema similar:** Imaginá que tenés que ordenar cartas de un mazo.

- Primero, necesitás un criterio de orden (¿por número? ¿por palo?)
- Luego, comparás de a pares para decidir cuál va primero
- Repetís hasta que todo esté ordenado

**La pregunta clave:** ¿Cómo decidís si un elemento va antes que otro?

Ahora pensá en tu problema:
- ¿Cuál es tu "criterio de orden"?
- ¿Cómo compararías dos elementos?

¿Ves la conexión entre este ejemplo y tu problema?"""

    def _get_fallback_clarification_request(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """Fallback para solicitud de clarificación cuando LLM no está disponible."""
        return """Para poder ayudarte mejor, necesito que seas más específico:

- ¿Qué parte exacta del problema te genera dificultad?
- ¿Qué intentaste hasta ahora?
- ¿Qué resultado esperabas vs. qué obtuviste?

Si tenés código, compartilo para poder ver dónde está el problema.
Por favor, reformulá tu pregunta con más detalles."""

    # FIX Cortez22 DEFECTO 1.1: Make async for future LLM integration
    async def _process_simulator_mode(
        self,
        session_id: str,
        prompt: str,
        strategy: Dict[str, Any],
        classification: Dict[str, Any],
        flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesa interacción en modo S-IA-X (Simulador)"""
        # Placeholder para simuladores
        # FIX Cortez22 DEFECTO 1.8: Use "response" not "message"
        logger.info(
            "Processing simulator mode",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "strategy_keys": sorted(strategy.keys()) if isinstance(strategy, dict) else []
            }
        )
        return {
            "response": "[Modo Simulador - En desarrollo]",
            "mode": "simulator",
            "metadata": {}
        }

    # FIX Cortez22 DEFECTO 1.1: Make async for future LLM integration
    async def _process_evaluator_mode(
        self,
        session_id: str,
        prompt: str,
        strategy: Dict[str, Any],
        classification: Dict[str, Any],
        flow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesa interacción en modo E-IA-Proc (Evaluador)"""
        # Placeholder para evaluador
        # FIX Cortez22 DEFECTO 1.8: Use "response" not "message"
        logger.info(
            "Processing evaluator mode",
            extra={
                "session_id": session_id,
                "flow_id": flow_id,
                "strategy_keys": sorted(strategy.keys()) if isinstance(strategy, dict) else []
            }
        )
        return {
            "response": "[Modo Evaluador - En desarrollo]",
            "mode": "evaluator",
            "metadata": {}
        }

    def _create_trace(
        self,
        session_id: str,
        student_id: str,
        activity_id: str,
        interaction_type: InteractionType,
        content: str,
        level: TraceLevel,
        **kwargs
    ) -> CognitiveTrace:
        """Crea una traza cognitiva (no la persiste aún)"""
        trace_id = str(uuid.uuid4())

        return CognitiveTrace(
            id=trace_id,
            session_id=session_id,
            student_id=student_id,
            activity_id=activity_id,
            trace_level=level,
            interaction_type=interaction_type,
            content=content,
            **kwargs
        )

    def _persist_trace(self, trace: CognitiveTrace) -> None:
        """Persiste una traza en BD (STATELESS)"""
        if self.trace_repo is not None:
            try:
                db_trace = self.trace_repo.create(trace)
                logger.debug(
                    "Trace persisted successfully",
                    extra={
                        "trace_id": db_trace.id,
                        "interaction_type": trace.interaction_type.value,
                        "session_id": trace.session_id,
                        "cognitive_state": trace.cognitive_state.value if trace.cognitive_state else None
                    }
                )
                # ✅ HIGH-01: Record Prometheus metric for trace creation
                metrics = _get_metrics()
                if metrics:
                    metrics.record_trace_creation(
                        trace_level=trace.trace_level.value if hasattr(trace.trace_level, 'value') else str(trace.trace_level),
                        interaction_type=trace.interaction_type.value if hasattr(trace.interaction_type, 'value') else str(trace.interaction_type)
                    )
            except Exception as e:
                logger.error(
                    "Failed to persist trace",
                    extra={
                        "error": str(e),
                        "session_id": trace.session_id,
                        "interaction_type": trace.interaction_type.value
                    },
                    exc_info=True
                )
        else:
            logger.warning(
                "Trace repository is None, cannot persist trace",
                extra={
                    "session_id": trace.session_id,
                    "interaction_type": trace.interaction_type.value
                }
            )
        # Si no hay repo, no hacer nada (backward compatibility)

    def _load_conversation_history(
        self,
        session_id: str,
        max_messages: int = 50  # FIX Cortez22 DEFECTO 1.7: Add limit parameter
    ) -> List[LLMMessage]:
        """
        ✅ NUEVO: Carga el historial de conversación de esta sesión como mensajes LLM.

        Recupera las trazas más recientes de la sesión y las convierte al formato de mensajes
        que espera el LLM provider, manteniendo el contexto de la conversación.

        FIX Cortez22 DEFECTO 1.7: Added limit to prevent OOM in long sessions

        Args:
            session_id: ID de la sesión actual
            max_messages: Límite máximo de mensajes a retornar (default: 50)

        Returns:
            Lista de LLMMessage con el historial formateado (últimos max_messages)
        """
        if self.trace_repo is None:
            logger.warning("No trace repository available for conversation history")
            return []

        try:
            # FIX Cortez22 DEFECTO 1.7: Add limit=100 to prevent loading ALL traces
            # This prevents OOM in sessions with thousands of interactions
            db_traces = self.trace_repo.get_by_session(session_id, limit=100)

            messages = []
            for trace in db_traces:
                # Agregar mensaje del usuario (STUDENT_PROMPT)
                if trace.interaction_type == InteractionType.STUDENT_PROMPT.value and trace.content:
                    messages.append(
                        LLMMessage(
                            role=LLMRole.USER,
                            content=trace.content
                        )
                    )

                # Agregar respuesta del asistente (AI_RESPONSE o TUTOR_INTERVENTION)
                elif trace.interaction_type in [
                    InteractionType.AI_RESPONSE.value,
                    InteractionType.TUTOR_INTERVENTION.value
                ] and trace.content:
                    messages.append(
                        LLMMessage(
                            role=LLMRole.ASSISTANT,
                            content=trace.content
                        )
                    )

            # FIX Cortez22 DEFECTO 1.7: Limit to last N messages to prevent LLM token explosion
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
                logger.info(
                    f"Truncated conversation history to last {max_messages} messages",
                    extra={"session_id": session_id, "original_count": len(messages) + (len(messages) - max_messages)}
                )

            logger.info(
                f"Loaded conversation history: {len(messages)} messages",
                extra={"session_id": session_id}
            )
            return messages
            
        except Exception as e:
            logger.error(
                f"Error loading conversation history: {e}",
                exc_info=True,
                extra={"session_id": session_id}
            )
            return []
    
    def _get_student_history(
        self,
        student_id: str,
        activity_id: Optional[str] = None
    ) -> List[CognitiveTrace]:
        """Obtiene el historial de trazas del estudiante desde BD (STATELESS)"""
        if self.trace_repo is None:
            return []  # Backward compatibility

        # ✅ STATELESS: Leer desde BD
        db_traces = self.trace_repo.get_by_student(student_id, limit=100)

        # Convertir de ORM a Pydantic
        traces = []
        for db_trace in db_traces:
            try:
                trace = CognitiveTrace(
                    id=db_trace.id,
                    session_id=db_trace.session_id,
                    student_id=db_trace.student_id,
                    activity_id=db_trace.activity_id,
                    trace_level=TraceLevel(db_trace.trace_level),
                    interaction_type=InteractionType(db_trace.interaction_type),
                    content=db_trace.content or "",
                    context=db_trace.context or {},
                    metadata=db_trace.trace_metadata or {},
                    cognitive_state=db_trace.cognitive_state,
                    ai_involvement=db_trace.ai_involvement or 0.5,
                )
                traces.append(trace)
            except Exception as e:
                # Skip invalid traces pero log the error
                logger.warning(
                    f"Failed to convert database trace to Pydantic model: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        "trace_id": db_trace.id if hasattr(db_trace, 'id') else 'unknown',
                        "session_id": db_trace.session_id if hasattr(db_trace, 'session_id') else 'unknown',
                        "student_id": student_id
                    }
                )
                continue

        # Filtrar por activity_id si se especificó
        if activity_id:
            traces = [t for t in traces if t.activity_id == activity_id]

        return traces

    def _create_risk(
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
        """Crea un objeto Risk (sin persistirlo aún)"""
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

    def _persist_risk(
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
        flow_id: Optional[str] = None,
        risk_repo_override: Optional[RiskRepositoryProtocol] = None,
        **kwargs
    ) -> Optional[Risk]:
        """Registra un riesgo detectado en BD (STATELESS)"""
        risk = Risk(
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

        repo = risk_repo_override or self.risk_repo

        # ✅ STATELESS: Persistir en BD
        if repo is not None:
            try:
                repo.create(risk)
                # ✅ Structured logging: Risk persisted successfully
                logger.info(
                    "Risk persisted to database",
                    extra={
                        "risk_id": risk.id,
                        "risk_type": risk_type.value,
                        "risk_level": risk_level.value,
                        "dimension": dimension.value,
                        "student_id": student_id,
                        "activity_id": activity_id,
                        "trace_count": len(trace_ids),
                        "flow_id": flow_id
                    }
                )
                # ✅ HIGH-01: Record Prometheus metric for risk detection
                metrics = _get_metrics()
                if metrics:
                    metrics.record_risk_detection(
                        risk_type=risk_type.value,
                        risk_level=risk_level.value,
                        dimension=dimension.value
                    )
            except Exception as e:
                # ✅ Structured logging: Risk persistence failed
                logger.error(
                    f"Failed to persist risk to database: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                    extra={
                        "risk_id": risk.id,
                        "risk_type": risk_type.value,
                        "risk_level": risk_level.value,
                        "student_id": student_id,
                        "activity_id": activity_id,
                        "flow_id": flow_id
                    }
                )
                # Re-raise to maintain error propagation
                raise
        else:
            # ✅ Structured logging: No repository available
            logger.warning(
                "Risk repository is None, cannot persist risk",
                extra={
                    "risk_id": risk.id,
                    "risk_type": risk_type.value,
                    "risk_level": risk_level.value,
                    "student_id": student_id,
                    "flow_id": flow_id
                }
            )

        return risk

    def _persist_risk_object(
        self,
        risk: Risk,
        flow_id: Optional[str] = None,
        risk_repo_override: Optional[RiskRepositoryProtocol] = None,
    ) -> None:
        """
        Persiste un objeto Risk existente en BD (STATELESS)

        Args:
            risk: Objeto Risk ya creado que se debe persistir
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
                    f"Failed to persist risk to database: {type(e).__name__}: {str(e)}",
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
                extra={"risk_id": risk.id, "risk_type": risk.risk_type.value, "flow_id": flow_id}
            )

    def _analyze_risks_async(
        self,
        session_id: str,
        input_trace: CognitiveTrace,
        response_trace: CognitiveTrace,
        classification: Dict[str, Any],
        flow_id: Optional[str] = None,
        risk_repo_override: Optional[RiskRepositoryProtocol] = None,
    ) -> None:
        """
        Análisis de riesgos asíncrono (AR-IA)

        Realiza análisis básico de riesgos a partir de las trazas de entrada y salida.
        En el MVP ejecuta sincrónicamente, en producción sería async (celery/rq).

        Args:
            session_id: ID de la sesión
            input_trace: Traza de entrada (prompt del estudiante)
            response_trace: Traza de salida (respuesta del agente)
            classification: Clasificación del prompt (tipo, delegación, etc.)

        Detecta:
        - RC1: Delegación total (solicitudes de código completo)
        - RC2: Dependencia excesiva de IA (alto ai_involvement)
        - RC3: Falta de justificación (decisiones sin explicación)
        - RE1: Integridad académica (uso no divulgado de IA)
        - REp1: Aceptación acrítica (no cuestiona respuestas de IA)
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
            return

        detected_risks = []

        # === RC1: Delegación Total ===
        # NOTE: cognitive_engine returns "is_total_delegation", not "is_delegation"
        if classification.get("is_total_delegation", False):
            delegation_signals = classification.get("delegation_signals", [])
            risk = self._create_risk(
                session_id=session_id,
                student_id=input_trace.student_id,
                activity_id=input_trace.activity_id,
                risk_type=RiskType.COGNITIVE_DELEGATION,
                risk_level=RiskLevel.HIGH,
                dimension=RiskDimension.COGNITIVE,
                description=(
                    "Intento de delegación total detectado. El estudiante solicita "
                    "soluciones completas sin descomposición del problema."
                ),
                evidence=[
                    input_trace.content[:200],  # First 200 chars of prompt
                    f"Señales: {', '.join(delegation_signals[:3])}"
                ],
                trace_ids=[input_trace.id, response_trace.id],
                root_cause="Tendencia a delegar la resolución completa a la IA sin esfuerzo propio",
                recommendations=[
                    "Solicitar descomposición explícita del problema en subtareas",
                    "Exigir justificación de cada paso antes de implementar",
                    "Reducir nivel de ayuda del tutor temporalmente",
                    "Asignar ejercicios similares sin acceso a IA"
                ],
                pedagogical_intervention=(
                    "Activar modo socrático estricto: solo preguntas guía, sin pistas directas"
                )
            )
            detected_risks.append(risk)
            self._persist_risk_object(
                risk,
                flow_id=flow_id,
                risk_repo_override=risk_repo_override,
            )

        # === RC2: Dependencia Excesiva de IA ===
        # Import constant to avoid hardcoded value
        from .constants import AI_DEPENDENCY_MEDIUM_THRESHOLD
        if input_trace.ai_involvement > AI_DEPENDENCY_MEDIUM_THRESHOLD:
            risk = self._create_risk(
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
                    "Fomentar resolución autónoma con menos asistencia de IA",
                    "Asignar ejercicios sin acceso a IA para desarrollar autonomía",
                    "Revisar interacciones previas para identificar patrón de dependencia"
                ]
            )
            detected_risks.append(risk)
            self._persist_risk_object(
                risk,
                flow_id=flow_id,
                risk_repo_override=risk_repo_override,
            )

        # === RC3: Falta de Justificación ===
        has_justification = (
            input_trace.decision_justification is not None and
            len(input_trace.decision_justification.strip()) > 20
        )
        if not has_justification and not classification.get("is_question", False):
            # Solo detectar si NO es una pregunta conceptual (donde no se espera justificación)
            risk = self._create_risk(
                session_id=session_id,
                student_id=input_trace.student_id,
                activity_id=input_trace.activity_id,
                risk_type=RiskType.LACK_JUSTIFICATION,
                risk_level=RiskLevel.LOW,
                dimension=RiskDimension.COGNITIVE,
                description=(
                    "El estudiante no proporciona justificación de sus decisiones o razonamiento. "
                    "Esto dificulta evaluar su proceso cognitivo."
                ),
                evidence=["No se detectó campo decision_justification"],
                trace_ids=[input_trace.id],
                recommendations=[
                    "Exigir explicitación del razonamiento en cada interacción",
                    "Solicitar que explique 'por qué' eligió cierto enfoque",
                    "Usar prompts estructurados que incluyan sección de justificación"
                ]
            )
            detected_risks.append(risk)
            self._persist_risk_object(
                risk,
                flow_id=flow_id,
                risk_repo_override=risk_repo_override,
            )

        # === REp1: Aceptación Acrítica ===
        # Detectar si el estudiante acepta respuestas sin cuestionarlas
        # (Simplificado: si ai_critiques es 0 y hay múltiples interacciones)
        if hasattr(response_trace, 'alternatives_considered'):
            alternatives = response_trace.alternatives_considered or []
            if len(alternatives) == 0 and input_trace.ai_involvement > 0.5:
                risk = self._create_risk(
                    session_id=session_id,
                    student_id=input_trace.student_id,
                    activity_id=input_trace.activity_id,
                    risk_type=RiskType.UNCRITICAL_ACCEPTANCE,
                    risk_level=RiskLevel.MEDIUM,
                    dimension=RiskDimension.EPISTEMIC,
                    description=(
                        "El estudiante no considera alternativas ni cuestiona las respuestas de la IA. "
                        "Esto indica posible aceptación acrítica."
                    ),
                    evidence=["No se registraron alternativas consideradas"],
                    trace_ids=[input_trace.id, response_trace.id],
                    recommendations=[
                        "Fomentar pensamiento crítico: '¿Qué otras opciones existen?'",
                        "Solicitar comparación entre diferentes enfoques",
                        "Pedir que identifique limitaciones de la solución propuesta"
                    ]
                )
                detected_risks.append(risk)
                self._persist_risk_object(risk, flow_id=flow_id)  # FIX: Persistir riesgo inmediatamente

        # Log summary
        if detected_risks:
            logger.warning(
                f"Risk analysis completed: {len(detected_risks)} risks detected",
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

        # FIX APPLIED: Risks are now persisted immediately via _persist_risk_object()
        # after each _create_risk() call above

    def get_trace_sequence(self, session_id: str) -> Optional[TraceSequence]:
        """Obtiene la secuencia de trazas de una sesión desde BD (STATELESS)"""
        if self.sequence_repo is None:
            return None  # Backward compatibility

        # ✅ STATELESS: Leer desde BD
        return self.sequence_repo.get_by_session(session_id)

    def get_risk_report(self, student_id: str, activity_id: str) -> Optional[RiskReport]:
        """Obtiene el reporte de riesgos desde BD (STATELESS)"""
        if self.risk_repo is None:
            return None  # Backward compatibility

        # ✅ STATELESS: Construir reporte desde BD
        risks = self.risk_repo.get_by_student(student_id)

        # Filtrar por activity_id
        risks = [r for r in risks if r.activity_id == activity_id]

        if not risks:
            return None

        # Construir RiskReport
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

    def _validate_interaction_input(
        self,
        session_id: str,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """
        Valida la entrada de una interacción.

        Args:
            session_id: ID de la sesión
            prompt: Prompt del estudiante
            context: Contexto adicional

        Raises:
            ValueError: Si la validación falla
        """
        from .constants import (
            PROMPT_MIN_LENGTH,
            PROMPT_MAX_LENGTH,
            CONTEXT_MAX_SIZE_BYTES,
            SESSION_ID_MAX_LENGTH
        )
        import json

        # Validar session_id
        if not session_id or not isinstance(session_id, str):
            raise ValueError("session_id debe ser un string no vacío")

        if len(session_id) > SESSION_ID_MAX_LENGTH:
            raise ValueError(
                f"session_id excede longitud máxima ({SESSION_ID_MAX_LENGTH} caracteres)"
            )

        # Validar prompt
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt debe ser un string no vacío")

        prompt_length = len(prompt.strip())
        if prompt_length < PROMPT_MIN_LENGTH:
            raise ValueError(
                f"Prompt demasiado corto (mínimo {PROMPT_MIN_LENGTH} caracteres)"
            )

        if prompt_length > PROMPT_MAX_LENGTH:
            raise ValueError(
                f"Prompt demasiado largo (máximo {PROMPT_MAX_LENGTH} caracteres)"
            )

        # Validar context
        if context is not None:
            if not isinstance(context, dict):
                raise ValueError("context debe ser un diccionario")

            # Validar tamaño del contexto
            try:
                context_size = len(json.dumps(context).encode('utf-8'))
                if context_size > CONTEXT_MAX_SIZE_BYTES:
                    raise ValueError(
                        f"Context demasiado grande (máximo {CONTEXT_MAX_SIZE_BYTES} bytes)"
                    )
            except (TypeError, ValueError) as e:
                raise ValueError(f"Context no es serializable a JSON: {str(e)}")

        logger.debug(
            "Input validation passed",
            extra={
                "session_id": session_id,
                "prompt_length": prompt_length,
                "has_context": context is not None
            }
        )

    def set_mode(self, session_id: str, mode: AgentMode) -> None:
        """Cambia el modo operativo de una sesión en BD (STATELESS)"""
        if self.session_repo is not None:
            self.session_repo.update_mode(session_id, mode.value.upper())
        # Si no hay repo, no hacer nada (backward compatibility)

    # =========================================================================
    # Circuit Breaker: Fallback Methods (cuando LLM falla o está inaccesible)
    # =========================================================================
    
    def _get_fallback_socratic_response(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """
        Fallback cuando Ollama está inaccesible - Respuesta Socrática
        
        Usa un banco de preguntas genéricas pero pedagógicamente válidas
        """
        logger.warning(
            "Using fallback Socratic response (LLM unavailable)",
            extra={"flow_id": flow_id} if flow_id else None
        )
        return """⚠️ El sistema de IA está experimentando dificultades temporales, pero puedo ayudarte con estas preguntas guía:

**Para ayudarte mejor, necesito entender tu proceso de pensamiento:**

1. ¿Qué entendés que te están pidiendo resolver?
2. ¿Qué conceptos creés que son relevantes para este problema?
3. ¿Cómo funcionaría una solución ideal?
4. ¿Qué has intentado hasta ahora y qué resultados obtuviste?

💡 **Tip**: Intenta descomponer el problema en partes más pequeñas y manejables.

_Responde estas preguntas y podremos continuar cuando el sistema se recupere._"""

    def _get_fallback_conceptual_explanation(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """
        Fallback cuando Ollama está inaccesible - Explicación Conceptual
        """
        logger.warning(
            "Using fallback conceptual explanation (LLM unavailable)",
            extra={"flow_id": flow_id} if flow_id else None
        )
        return """⚠️ El sistema de IA está temporalmente fuera de servicio.

**Mientras tanto, aquí tienes una estructura para explorar el concepto:**

**Concepto clave**: [Identifica el concepto central de tu pregunta]

**Principio fundamental**: 
- ¿Por qué es importante este concepto en programación?
- ¿Qué problema resuelve?

**Ejemplo simple**: 
- Busca en tu material de estudio un ejemplo concreto
- Intenta relacionarlo con situaciones de la vida real

**Aplicación práctica**: 
- ¿Cómo lo usarías en un proyecto real?
- ¿Qué ventajas te daría?

📚 **Recomendación**: Consulta la documentación oficial del lenguaje o framework que estás usando.

_El sistema estará disponible nuevamente en breve._"""

    def _get_fallback_guided_hints(self, prompt: str, flow_id: Optional[str] = None) -> str:
        """
        Fallback cuando Ollama está inaccesible - Pistas Guiadas
        """
        logger.warning(
            "Using fallback guided hints (LLM unavailable)",
            extra={"flow_id": flow_id} if flow_id else None
        )
        return """⚠️ El asistente de IA está temporalmente inaccesible.

**Aquí tienes una estrategia general de resolución de problemas:**

**Pista 1 - Descomponer**: 
- Divide el problema en subproblemas más pequeños
- Resuelve cada parte por separado

**Pista 2 - Estructuras de datos**: 
- ¿Qué estructura (lista, diccionario, conjunto) facilitaría la solución?
- ¿Necesitas acceso rápido, orden, o valores únicos?

**Pista 3 - Casos especiales**: 
- No olvides casos límite (vacío, un solo elemento, valores extremos)
- Prueba tu lógica con ejemplos simples primero

**Pista 4 - Algoritmo paso a paso**: 
- Escribe en pseudocódigo antes de programar
- Verifica cada paso con un ejemplo concreto

**Próximo paso**: Intenta escribir el esqueleto de la solución primero, sin preocuparte por los detalles.

🔧 **Herramientas**: Usa print() o debugger para entender qué está haciendo tu código en cada paso.

_El sistema de IA volverá pronto. Mientras tanto, estos pasos pueden ayudarte a avanzar._"""