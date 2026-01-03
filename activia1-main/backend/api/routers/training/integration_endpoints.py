"""
Training Integration Endpoints - API routes for Digital Trainer + Agent Integration.

Cortez50: New file for Digital Trainer integration with T-IA-Cog and N4 traceability.

Contains endpoints for:
- /pista/v2: Contextual hints using T-IA-Cog
- /reflexion: Post-exercise reflection capture
- /sesion/{id}/proceso: Process analysis
- /submit/v2: Extended submission with traceability
"""

from fastapi import APIRouter, Depends, BackgroundTasks
# FIX Cortez53: Removed HTTPException, status - using custom exceptions
from ...exceptions import (
    AINativeAPIException,
    TrainingSessionNotFoundError,
    TrainingSessionAccessDeniedError,
    TrainingOperationError,
)
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import logging

from backend.database.config import get_db
from backend.api.deps import get_current_user, get_llm_provider
from backend.database.models import UserDB as User
from backend.api import config as app_config

from .schemas import (
    # V2 Schemas
    SolicitarPistaV2Request,
    PistaV2Response,
    HelpLevelEnum,
    ReflexionRequest,
    ReflexionResponse,
    ProcesoRequest,
    ProcesoAnalisis,
    TraceResumen,
    RiskFlag,
    CognitiveStateEnum,
    RiskTypeEnum,
    RiskSeverityEnum,
    SubmitEjercicioV2Request,
    SubmitEjercicioV2Response,
    EjercicioActual,
)
from .session_storage import obtener_sesion, guardar_sesion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["Digital Training V2"])


def get_feature_flags() -> Dict[str, bool]:
    """Get feature flags for training integration."""
    return {
        "training_use_tutor_hints": getattr(app_config, "TRAINING_USE_TUTOR_HINTS", False),
        "training_n4_tracing": getattr(app_config, "TRAINING_N4_TRACING", False),
        "training_risk_monitor": getattr(app_config, "TRAINING_RISK_MONITOR", False),
    }


def is_feature_enabled(feature: str) -> bool:
    """Check if a feature flag is enabled."""
    flags = get_feature_flags()
    return flags.get(feature, False)


# =============================================================================
# PISTA V2 - Contextual Hints with T-IA-Cog
# =============================================================================

@router.post("/pista/v2", response_model=PistaV2Response)
async def solicitar_pista_v2(
    request: SolicitarPistaV2Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 HIGH-API-002
    llm_provider: Optional[Any] = Depends(get_llm_provider),
):
    """
    Solicita una pista contextual usando T-IA-Cog.

    A diferencia de /pista (que devuelve pistas estaticas), este endpoint:
    - Construye un "prompt implicito" del contexto del estudiante
    - Usa T-IA-Cog para generar pistas pedagogicas contextuales
    - Registra la solicitud como traza cognitiva (si N4 habilitado)
    - Aplica los 4 niveles de ayuda (minimo, bajo, medio, alto)

    Feature Flags:
    - TRAINING_USE_TUTOR_HINTS: Si True, usa LLM para generar pistas
    - TRAINING_N4_TRACING: Si True, registra traza de solicitud
    """
    try:
        # Validate session
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionAccessDeniedError()

        # Get current exercise
        index_actual = sesion['ejercicio_actual_index']
        ejercicio = sesion['ejercicios'][index_actual]

        # Map hint number to help level
        level_map = {
            1: HelpLevelEnum.MINIMO,
            2: HelpLevelEnum.BAJO,
            3: HelpLevelEnum.MEDIO,
            4: HelpLevelEnum.ALTO,
        }
        help_level = level_map.get(request.numero_pista, HelpLevelEnum.MEDIO)

        # Check feature flag for T-IA-Cog integration
        use_llm_hints = is_feature_enabled("training_use_tutor_hints")

        if use_llm_hints and llm_provider:
            # Use TrainingHintsStrategy for contextual hints
            try:
                from backend.agents.tutor_modes import (
                    TrainingHintsStrategy,
                    ExerciseContext,
                    AttemptContext,
                    TrainingHintRequest,
                )

                strategy = TrainingHintsStrategy()

                # Build exercise context
                exercise_ctx = ExerciseContext(
                    exercise_id=ejercicio.get('id', f"ex_{index_actual}"),
                    title=ejercicio.get('titulo', 'Ejercicio'),
                    description=ejercicio.get('consigna', ''),
                    expected_concepts=ejercicio.get('conceptos', []),
                    difficulty=ejercicio.get('dificultad', 'basico'),
                    language=sesion.get('language', 'python'),
                    hints_available=ejercicio.get('pistas', []),
                )

                # Build attempt context
                attempt_ctx = AttemptContext(
                    attempt_number=sesion.get('intentos_ejercicio_actual', 0),
                    last_code=request.codigo_actual,
                    last_error=request.ultimo_error,
                    previous_hints_requested=sesion.get('pistas_usadas', 0),
                )

                # Build hint request
                hint_request = TrainingHintRequest(
                    session_id=request.session_id,
                    student_id=str(current_user.id),
                    hint_number=request.numero_pista,
                    exercise=exercise_ctx,
                    attempts=attempt_ctx,
                )

                # Generate contextual hint
                response = await strategy.generate_training_hint(
                    hint_request,
                    llm_provider=llm_provider,
                )

                # Update session
                if 'pistas_usadas' not in sesion:
                    sesion['pistas_usadas'] = 0
                sesion['pistas_usadas'] = max(sesion['pistas_usadas'], request.numero_pista)
                guardar_sesion(request.session_id, sesion)

                # Record trace if N4 enabled
                if is_feature_enabled("training_n4_tracing"):
                    background_tasks.add_task(
                        _record_hint_trace,
                        session_id=request.session_id,
                        student_id=str(current_user.id),
                        exercise_id=ejercicio.get('id', ''),
                        hint_number=request.numero_pista,
                        help_level=help_level.value,
                    )

                return PistaV2Response(
                    contenido=response.message,
                    numero=request.numero_pista,
                    nivel_ayuda=help_level,
                    total_pistas=4,
                    requiere_reflexion=response.requires_student_response,
                    pregunta_seguimiento=response.metadata.get('follow_up_question'),
                    metadata={
                        "cognitive_state": response.metadata.get('cognitive_state'),
                        "generated_with_llm": True,
                        "hints_count": response.hints_count,
                    }
                )

            except ImportError as e:
                logger.warning("TrainingHintsStrategy not available, falling back: %s", e)
            except Exception as e:
                logger.warning("LLM hint generation failed, using fallback: %s", e)

        # Fallback to static hints
        pistas = ejercicio.get('pistas', [])
        if not pistas:
            # Generate generic hint based on level
            contenido = _generate_generic_hint(help_level, ejercicio, request.ultimo_error)
        elif request.numero_pista <= len(pistas):
            contenido = pistas[request.numero_pista - 1]
        else:
            contenido = pistas[-1] if pistas else "No hay mas pistas disponibles."

        # Update session
        if 'pistas_usadas' not in sesion:
            sesion['pistas_usadas'] = 0
        sesion['pistas_usadas'] = max(sesion['pistas_usadas'], request.numero_pista)
        guardar_sesion(request.session_id, sesion)

        return PistaV2Response(
            contenido=contenido,
            numero=request.numero_pista,
            nivel_ayuda=help_level,
            total_pistas=4,
            requiere_reflexion=True,
            pregunta_seguimiento="Que vas a intentar ahora con esta informacion?",
            metadata={"generated_with_llm": False}
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error("Error en pista/v2: %s", e, exc_info=True)
        # FIX Cortez53: Use custom exception
        raise TrainingOperationError("obtener la pista contextual")


def _generate_generic_hint(
    level: HelpLevelEnum,
    ejercicio: Dict[str, Any],
    ultimo_error: Optional[str]
) -> str:
    """Generate a generic hint when static hints are not available."""
    titulo = ejercicio.get('titulo', 'el ejercicio')

    if level == HelpLevelEnum.MINIMO:
        return f"""**Pista Nivel 1 - Preguntas Orientadoras**

Antes de darte mas informacion, reflexionemos:
1. Que datos de entrada recibe tu solucion?
2. Que transformacion necesitas aplicar?
3. Como verificarias que tu resultado es correcto?

Intenta responder estas preguntas antes de pedir mas ayuda."""

    elif level == HelpLevelEnum.BAJO:
        hint = f"""**Pista Nivel 2 - Conceptual**

Para resolver '{titulo}', piensa en los conceptos fundamentales:
- Identifica el patron del problema
- Considera que estructuras de datos son apropiadas
- Recuerda las operaciones basicas disponibles"""

        if ultimo_error:
            hint += f"\n\nTu ultimo error sugiere revisar: tipos de datos y operaciones compatibles."

        return hint

    elif level == HelpLevelEnum.MEDIO:
        return f"""**Pista Nivel 3 - Estrategia**

Enfoque sugerido para '{titulo}':

1. **Entrada**: Identifica y valida los datos de entrada
2. **Procesamiento**: Aplica la transformacion necesaria
3. **Salida**: Retorna el resultado en el formato esperado

```pseudocodigo
funcion resolver(entrada):
    // Paso 1: Preparar datos
    // Paso 2: Procesar
    // Paso 3: Retornar
```

Que paso implementarias primero?"""

    else:  # ALTO
        return f"""**Pista Nivel 4 - Detallada**

Estrategia completa para '{titulo}':

1. Descompone el problema en subproblemas
2. Resuelve cada subproblema por separado
3. Combina las soluciones

Si aun tenes dificultades, el problema probablemente
esta en un detalle especifico. Revisa:
- Inicializacion de variables
- Condiciones de los bucles
- Tipos de datos en operaciones

Con esta guia, deberias poder avanzar.
Que linea de codigo escribirias primero?"""


async def _record_hint_trace(
    session_id: str,
    student_id: str,
    exercise_id: str,
    hint_number: int,
    help_level: str,
) -> None:
    """Background task to record hint request trace."""
    try:
        from backend.core.training_traceability import TrainingTraceCollector

        collector = TrainingTraceCollector()
        await collector.trace_hint_request(
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            hint_number=hint_number,
            help_level=help_level,
        )
        logger.debug("Hint trace recorded for session %s", session_id)
    except Exception as e:
        # FIX Cortez67 (MEDIUM-002): Add exc_info for stack trace
        logger.error("Failed to record hint trace: %s", e, exc_info=True)


# =============================================================================
# REFLEXION - Post-Exercise Reflection Capture
# =============================================================================

@router.post("/reflexion", response_model=ReflexionResponse)
async def capturar_reflexion(
    request: ReflexionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 HIGH-API-002
):
    """
    Captura la reflexion post-ejercicio del estudiante.

    Este endpoint implementa la "Trazabilidad Activa" del modelo hibrido N4:
    - El estudiante reflexiona explicitamente sobre su proceso
    - Se captura dimension cognitiva, metacognicion y aprendizaje
    - Se registra como traza N4 con dimension METACOGNITIVA

    Feature Flags:
    - TRAINING_N4_TRACING: Si True, registra traza completa
    """
    try:
        # Validate session
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionAccessDeniedError()

        # Analyze reflection depth
        reflection_depth = _analyze_reflection_depth(request)

        # Infer cognitive dimension from reflection content
        cognitive_dimension = _infer_cognitive_dimension(request)

        # Calculate XP bonus based on reflection quality
        xp_bonus = _calculate_reflection_xp(reflection_depth)

        # Generate trace ID
        trace_id = str(uuid.uuid4())

        # Record trace if N4 enabled
        if is_feature_enabled("training_n4_tracing"):
            background_tasks.add_task(
                _record_reflection_trace,
                trace_id=trace_id,
                session_id=request.session_id,
                student_id=str(current_user.id),
                exercise_id=request.exercise_id,
                reflection_data={
                    "que_fue_dificil": request.que_fue_dificil,
                    "como_lo_resolvi": request.como_lo_resolvi,
                    "que_aprendi": request.que_aprendi,
                    "alternativas_consideradas": request.alternativas_consideradas,
                    "errores_cometidos": request.errores_cometidos,
                },
                reflection_depth=reflection_depth,
                cognitive_dimension=cognitive_dimension,
            )

        # Update session with reflection count
        if 'reflexiones_capturadas' not in sesion:
            sesion['reflexiones_capturadas'] = 0
        sesion['reflexiones_capturadas'] += 1
        guardar_sesion(request.session_id, sesion)

        return ReflexionResponse(
            trace_id=trace_id,
            mensaje="Reflexion capturada exitosamente. Tu analisis ayuda a mejorar tu proceso de aprendizaje.",
            dimension_cognitiva_inferida=cognitive_dimension,
            nivel_metacognitivo=reflection_depth,
            xp_bonus=xp_bonus,
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error("Error en reflexion: %s", e, exc_info=True)
        # FIX Cortez53: Use custom exception
        raise TrainingOperationError("capturar la reflexion")


def _analyze_reflection_depth(request: ReflexionRequest) -> str:
    """Analyze the depth of student's reflection."""
    # Calculate total reflection length
    total_length = len(request.que_fue_dificil) + len(request.como_lo_resolvi) + len(request.que_aprendi)

    # Check for optional fields
    has_alternatives = bool(request.alternativas_consideradas and len(request.alternativas_consideradas) > 20)
    has_errors = bool(request.errores_cometidos and len(request.errores_cometidos) > 20)

    # Determine depth level
    if total_length > 300 and has_alternatives and has_errors:
        return "profundo"
    elif total_length > 150 or has_alternatives or has_errors:
        return "moderado"
    else:
        return "superficial"


def _infer_cognitive_dimension(request: ReflexionRequest) -> str:
    """Infer the dominant cognitive dimension from reflection."""
    text = f"{request.que_fue_dificil} {request.como_lo_resolvi} {request.que_aprendi}".lower()

    # Keywords for each dimension
    dimensions = {
        "metacognitiva": ["pense", "razone", "estrategia", "enfoque", "planifique", "reflexione"],
        "procedimental": ["paso", "hice", "ejecute", "implemente", "codigo", "funcion"],
        "conceptual": ["concepto", "entendi", "teoria", "principio", "idea", "aprendi"],
        "afectiva": ["senti", "frustre", "logre", "satisfecho", "dificil", "facil"],
    }

    # Count matches
    scores = {dim: sum(1 for kw in keywords if kw in text) for dim, keywords in dimensions.items()}

    # Return highest scoring dimension
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "procedimental"


def _calculate_reflection_xp(depth: str) -> int:
    """Calculate XP bonus based on reflection depth."""
    xp_map = {
        "profundo": 50,
        "moderado": 25,
        "superficial": 10,
    }
    return xp_map.get(depth, 10)


async def _record_reflection_trace(
    trace_id: str,
    session_id: str,
    student_id: str,
    exercise_id: str,
    reflection_data: Dict[str, Any],
    reflection_depth: str,
    cognitive_dimension: str,
) -> None:
    """Background task to record reflection trace."""
    try:
        from backend.core.training_traceability import TrainingTraceCollector

        collector = TrainingTraceCollector()
        await collector.trace_reflection(
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            what_was_difficult=reflection_data["que_fue_dificil"],
            how_solved=reflection_data["como_lo_resolvi"],
            what_learned=reflection_data["que_aprendi"],
            alternatives_considered=reflection_data.get("alternativas_consideradas"),
            errors_made=reflection_data.get("errores_cometidos"),
        )
        logger.debug("Reflection trace %s recorded for session %s", trace_id, session_id)
    except Exception as e:
        # FIX Cortez67 (MEDIUM-002): Add exc_info for stack trace
        logger.error("Failed to record reflection trace: %s", e, exc_info=True)


# =============================================================================
# PROCESO - Session Process Analysis
# =============================================================================

@router.get("/sesion/{session_id}/proceso", response_model=ProcesoAnalisis)
async def obtener_analisis_proceso(
    session_id: str,
    request: ProcesoRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 HIGH-API-002
):
    """
    Obtiene el analisis del proceso cognitivo de una sesion.

    Este endpoint proporciona:
    - Resumen de trazas cognitivas
    - Estados cognitivos mas frecuentes
    - Transiciones y cambios de estrategia
    - Riesgos detectados
    - Indices de autonomia y reflexion
    - Recomendaciones pedagogicas

    Feature Flags:
    - TRAINING_N4_TRACING: Si False, retorna analisis basico
    """
    try:
        # Validate session
        sesion = obtener_sesion(session_id)
        if not sesion:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionAccessDeniedError()

        # Check if N4 tracing is enabled
        if is_feature_enabled("training_n4_tracing"):
            try:
                from backend.core.training_traceability import TrainingTraceCollector

                collector = TrainingTraceCollector()
                analysis = await collector.get_process_analysis(
                    session_id=session_id,
                    student_id=str(current_user.id),
                )

                if analysis:
                    return _convert_analysis_to_response(
                        analysis,
                        session_id,
                        str(current_user.id),
                        request,
                    )
            except Exception as e:
                logger.warning("N4 analysis failed, using basic: %s", e)

        # Fallback to basic analysis from session data
        return _generate_basic_analysis(sesion, session_id, str(current_user.id), request)

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error("Error en proceso: %s", e, exc_info=True)
        # FIX Cortez53: Use custom exception
        raise TrainingOperationError("obtener el analisis de proceso")


def _convert_analysis_to_response(
    analysis: Dict[str, Any],
    session_id: str,
    student_id: str,
    request: ProcesoRequest,
) -> ProcesoAnalisis:
    """Convert internal analysis to API response."""
    trazas_resumen = []
    if request.incluir_trazas:
        for trace in analysis.get("traces", [])[:20]:  # Limit to 20
            trazas_resumen.append(TraceResumen(
                timestamp=trace.get("timestamp", datetime.now()),
                tipo=trace.get("type", "unknown"),
                estado_cognitivo=CognitiveStateEnum(trace.get("cognitive_state", "exploracion")),
                confianza_inferencia=trace.get("confidence", "medium"),
                metadata=trace.get("metadata", {}),
            ))

    riesgos = []
    if request.incluir_riesgos:
        for risk in analysis.get("risks", []):
            riesgos.append(RiskFlag(
                tipo=RiskTypeEnum(risk.get("type", "frustration")),
                severidad=RiskSeverityEnum(risk.get("severity", "low")),
                mensaje=risk.get("message", ""),
                detectado_en=risk.get("detected_at", datetime.now()),
                resuelto=risk.get("resolved", False),
            ))

    recomendaciones = []
    if request.incluir_recomendaciones:
        recomendaciones = analysis.get("recommendations", [])

    return ProcesoAnalisis(
        session_id=session_id,
        student_id=student_id,
        total_trazas=analysis.get("total_traces", 0),
        trazas_resumen=trazas_resumen,
        estados_mas_frecuentes=analysis.get("most_frequent_states", []),
        transiciones_cognitivas=analysis.get("cognitive_transitions", 0),
        cambios_estrategia=analysis.get("strategy_changes", 0),
        tiempo_por_estado=analysis.get("time_per_state", {}),
        riesgos_detectados=riesgos,
        indice_autonomia=analysis.get("autonomy_index", 0.5),
        indice_reflexion=analysis.get("reflection_index", 0.0),
        recomendaciones=recomendaciones,
    )


def _generate_basic_analysis(
    sesion: Dict[str, Any],
    session_id: str,
    student_id: str,
    request: ProcesoRequest,
) -> ProcesoAnalisis:
    """Generate basic analysis from session data when N4 is not available."""
    # Calculate basic metrics
    total_ejercicios = sesion.get('total_ejercicios', 0)
    ejercicios_completados = len(sesion.get('resultados', []))
    pistas_usadas = sesion.get('pistas_usadas', 0)
    reflexiones = sesion.get('reflexiones_capturadas', 0)

    # Basic autonomy index (0-1)
    if total_ejercicios > 0:
        autonomy = 1.0 - (pistas_usadas / (total_ejercicios * 4))  # Max 4 hints per exercise
        autonomy = max(0.0, min(1.0, autonomy))
    else:
        autonomy = 0.5

    # Reflection index
    reflection_index = min(1.0, reflexiones / max(1, ejercicios_completados))

    # Basic recommendations
    recomendaciones = []
    if request.incluir_recomendaciones:
        if pistas_usadas > total_ejercicios * 2:
            recomendaciones.append(
                "Considera intentar resolver mas ejercicios de forma independiente antes de pedir pistas."
            )
        if reflexiones < ejercicios_completados:
            recomendaciones.append(
                "La reflexion post-ejercicio ayuda a consolidar el aprendizaje. Intenta reflexionar despues de cada ejercicio."
            )
        if autonomy > 0.7:
            recomendaciones.append(
                "Excelente trabajo autonomo! Sigue asi."
            )

    return ProcesoAnalisis(
        session_id=session_id,
        student_id=student_id,
        total_trazas=ejercicios_completados + pistas_usadas + reflexiones,
        trazas_resumen=[],  # No traces available in basic mode
        estados_mas_frecuentes=["implementacion", "depuracion"],
        transiciones_cognitivas=ejercicios_completados * 2,  # Estimate
        cambios_estrategia=pistas_usadas,  # Each hint might indicate strategy change
        tiempo_por_estado={},  # Not available in basic mode
        riesgos_detectados=[],  # Not available in basic mode
        indice_autonomia=autonomy,
        indice_reflexion=reflection_index,
        recomendaciones=recomendaciones,
    )


# =============================================================================
# SUBMIT V2 - Extended Submission with Traceability
# =============================================================================

@router.post("/submit/v2", response_model=SubmitEjercicioV2Response)
async def submit_ejercicio_v2(
    request: SubmitEjercicioV2Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 HIGH-API-002
):
    """
    Envia codigo con contexto adicional para trazabilidad.

    Extension de /submit-ejercicio que incluye:
    - Deteccion de copy-paste
    - Tiempo entre submissions
    - Registro de traza cognitiva (si N4 habilitado)
    - Deteccion de riesgos (si habilitado)

    Feature Flags:
    - TRAINING_N4_TRACING: Registra trazas cognitivas
    - TRAINING_RISK_MONITOR: Detecta riesgos en tiempo real
    """
    try:
        # Import the original submit logic
        from .endpoints import router as original_router
        from .schemas import SubmitEjercicioRequest

        # Validate session
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            # FIX Cortez53: Use custom exception
            raise TrainingSessionAccessDeniedError()

        # Get current exercise info
        index_actual = sesion['ejercicio_actual_index']
        ejercicio = sesion['ejercicios'][index_actual]
        exercise_id = ejercicio.get('id', f"ex_{index_actual}")

        # Track attempt number
        if 'intentos_ejercicio_actual' not in sesion:
            sesion['intentos_ejercicio_actual'] = 0
        sesion['intentos_ejercicio_actual'] += 1
        attempt_number = sesion['intentos_ejercicio_actual']

        # Risk detection (if enabled)
        risk_flags = []
        inferred_state = CognitiveStateEnum.IMPLEMENTACION

        if is_feature_enabled("training_risk_monitor"):
            try:
                from backend.core.training_risk_monitor import TrainingRiskMonitor

                monitor = TrainingRiskMonitor()
                risk_result = await monitor.analyze_attempt(
                    session_id=request.session_id,
                    student_id=str(current_user.id),
                    exercise_id=exercise_id,
                    code=request.codigo_usuario,
                    attempt_number=attempt_number,
                    time_since_last_seconds=(request.tiempo_desde_ultimo_ms or 0) / 1000,
                    test_result=None,  # Will be updated after execution
                )

                for rf in risk_result.get("risk_flags", []):
                    risk_flags.append(RiskFlag(
                        tipo=RiskTypeEnum(rf.get("type", "frustration")),
                        severidad=RiskSeverityEnum(rf.get("severity", "low")),
                        mensaje=rf.get("message", ""),
                        detectado_en=datetime.now(),
                        resuelto=False,
                    ))

            except Exception as e:
                logger.warning("Risk monitor failed: %s", e)

        # Copy-paste detection
        if request.es_codigo_pegado:
            risk_flags.append(RiskFlag(
                tipo=RiskTypeEnum.COPY_PASTE,
                severidad=RiskSeverityEnum.MEDIUM,
                mensaje="Codigo detectado como pegado. Asegurate de entender lo que hace.",
                detectado_en=datetime.now(),
                resuelto=False,
            ))

        # Execute tests (simplified - actual implementation would call sandbox)
        tests = ejercicio.get('tests', [])
        # For now, we'll simulate - in production this would call the sandbox
        tests_passed = 0
        tests_total = len(tests)
        correcto = False
        mensaje = "Ejecutando tests..."

        # Record trace if N4 enabled
        trace_id = None
        if is_feature_enabled("training_n4_tracing"):
            trace_id = str(uuid.uuid4())
            background_tasks.add_task(
                _record_attempt_trace,
                trace_id=trace_id,
                session_id=request.session_id,
                student_id=str(current_user.id),
                exercise_id=exercise_id,
                code=request.codigo_usuario,
                attempt_number=attempt_number,
                time_since_last_seconds=(request.tiempo_desde_ultimo_ms or 0) / 1000,
            )

        # Update session
        guardar_sesion(request.session_id, sesion)

        # Build response
        return SubmitEjercicioV2Response(
            correcto=correcto,
            tests_pasados=tests_passed,
            tests_totales=tests_total,
            mensaje=mensaje,
            siguiente_ejercicio=None,
            finalizado=False,
            resultado_final=None,
            trace_id=trace_id,
            estado_cognitivo_inferido=inferred_state,
            riesgos_activos=risk_flags,
        )

    except AINativeAPIException:
        raise
    except Exception as e:
        logger.error("Error en submit/v2: %s", e, exc_info=True)
        # FIX Cortez53: Use custom exception
        raise TrainingOperationError("procesar el codigo")


async def _record_attempt_trace(
    trace_id: str,
    session_id: str,
    student_id: str,
    exercise_id: str,
    code: str,
    attempt_number: int,
    time_since_last_seconds: float,
) -> None:
    """Background task to record code attempt trace."""
    try:
        from backend.core.training_traceability import TrainingTraceCollector

        collector = TrainingTraceCollector()
        await collector.trace_code_attempt(
            session_id=session_id,
            student_id=student_id,
            exercise_id=exercise_id,
            code=code,
            result=None,  # Would be passed from actual execution
            attempt_number=attempt_number,
            previous_code=None,
            time_since_last_seconds=time_since_last_seconds,
        )
        logger.debug("Attempt trace %s recorded for session %s", trace_id, session_id)
    except Exception as e:
        # FIX Cortez67 (MEDIUM-002): Add exc_info for stack trace
        logger.error("Failed to record attempt trace: %s", e, exc_info=True)
