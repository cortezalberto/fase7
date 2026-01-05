"""
Router para herramientas de docentes

Sprint 3 - HU-DOC-002, HU-DOC-003, HU-DOC-004
FIX Cortez51: Removed unused imports (func, PaginationParams)
FIX Cortez52: Fixed N+1 queries using batch loading methods
"""
from fastapi import APIRouter, Depends, Query
# FIX Cortez53: Removed HTTPException, status - using custom exceptions
from ..exceptions import TooManyStudentsError, NoSessionsFoundError
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timezone

from backend.core.constants import utc_now


def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware (UTC) for comparison.

    FIX Cortez79: PostgreSQL returns naive datetimes, but utc_now() returns aware.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
from ..deps import get_db, get_session_repository, get_trace_repository, get_risk_repository, require_teacher_role, get_intervention_repository
from ..schemas.common import APIResponse
from ...database.repositories import SessionRepository, TraceRepository, RiskRepository, InterventionRepository

router = APIRouter(prefix="/teacher", tags=["Teacher Tools"])


# FIX EP-6: Maximum number of students for comparison to prevent performance issues
MAX_STUDENTS_COMPARE = 50


@router.get(
    "/students/compare",
    summary="Comparar procesos cognitivos de múltiples estudiantes",
    description="Compara los caminos cognitivos de diferentes estudiantes en la misma actividad (HU-DOC-003). Requiere rol teacher."
)
async def compare_students(
    activity_id: str = Query(..., description="ID de la actividad"),
    student_ids: List[str] = Query(None, description=f"IDs específicos de estudiantes (opcional, máximo {MAX_STUDENTS_COMPARE})"),
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Compara los procesos cognitivos de múltiples estudiantes en la misma actividad.

    **HU-DOC-003**: Permite al docente identificar patrones, dificultades comunes
    y estrategias exitosas.

    **Métricas comparadas:**
    - Tiempo promedio de resolución
    - Distribución de estados cognitivos
    - Patrones de uso de IA
    - Riesgos más frecuentes
    - Estrategias exitosas vs fallidas

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/students/compare?activity_id=prog2_tp1_colas
    GET /api/v1/teacher/students/compare?activity_id=prog2_tp1_colas&student_ids=student_001&student_ids=student_002
    ```
    """
    # FIX EP-6: Validate student_ids limit to prevent performance issues
    # FIX Cortez53: Use custom exception
    if student_ids and len(student_ids) > MAX_STUDENTS_COMPARE:
        raise TooManyStudentsError(len(student_ids), MAX_STUDENTS_COMPARE)

    # Obtener todas las sesiones de la actividad
    all_sessions = session_repo.get_by_activity(activity_id)

    if not all_sessions:
        # FIX Cortez53: Use custom exception
        raise NoSessionsFoundError(activity_id=activity_id)

    # Filtrar por estudiantes específicos si se proporcionaron
    if student_ids:
        sessions = [s for s in all_sessions if s.student_id in student_ids]
    else:
        sessions = all_sessions

    if not sessions:
        # FIX Cortez53: Use custom exception
        raise NoSessionsFoundError(activity_id=activity_id, student_ids=student_ids)

    # FIX Cortez52: Batch load all traces and risks to avoid N+1 queries
    session_ids = [s.id for s in sessions]
    all_traces_by_session = trace_repo.get_by_session_ids(session_ids)
    all_risks_by_session = risk_repo.get_by_session_ids(session_ids)

    # Construir comparativa
    students_data = []

    for session in sessions:
        # FIX Cortez52: Use pre-loaded data instead of per-session queries
        traces = all_traces_by_session.get(session.id, [])
        risks = all_risks_by_session.get(session.id, [])

        # Calcular duración
        duration_minutes = 0.0
        if session.end_time:
            duration_minutes = (session.end_time - session.start_time).total_seconds() / 60.0

        # Estados cognitivos visitados
        cognitive_states = list(set(t.cognitive_state for t in traces if t.cognitive_state))

        # Promedio de AI involvement
        ai_involvements = [t.ai_involvement or 0.0 for t in traces]
        ai_dependency_avg = sum(ai_involvements) / len(ai_involvements) if ai_involvements else 0.0

        # Riesgos por tipo
        risks_by_type = defaultdict(int)
        for risk in risks:
            risks_by_type[risk.risk_type] += 1

        # Interacciones bloqueadas
        blocked_count = sum(
            1 for t in traces
            if t.trace_metadata and t.trace_metadata.get("blocked")
        )

        students_data.append({
            "student_id": session.student_id,
            "session_id": session.id,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "duration_minutes": round(duration_minutes, 2),
            "total_interactions": len(traces),
            "blocked_interactions": blocked_count,
            "cognitive_states_visited": cognitive_states,
            "ai_dependency_average": round(ai_dependency_avg, 2),
            "risks_total": len(risks),
            "risks_by_type": dict(risks_by_type),
            "status": session.status
        })

    # Calcular estadísticas agregadas
    completed_sessions = [s for s in students_data if s["status"] == "completed"]

    if completed_sessions:
        avg_duration = sum(s["duration_minutes"] for s in completed_sessions) / len(completed_sessions)
        avg_interactions = sum(s["total_interactions"] for s in completed_sessions) / len(completed_sessions)
        avg_ai_dependency = sum(s["ai_dependency_average"] for s in completed_sessions) / len(completed_sessions)
    else:
        avg_duration = 0.0
        avg_interactions = 0.0
        avg_ai_dependency = 0.0

    # Riesgos más comunes
    all_risks = defaultdict(int)
    for student in students_data:
        for risk_type, count in student["risks_by_type"].items():
            all_risks[risk_type] += count

    top_risks = sorted(all_risks.items(), key=lambda x: x[1], reverse=True)[:5]

    # Estados cognitivos más frecuentes
    all_states = defaultdict(int)
    for student in students_data:
        for state in student["cognitive_states_visited"]:
            all_states[state] += 1

    # Preparar respuesta
    comparison = {
        "activity_id": activity_id,
        "students_count": len(students_data),
        "completed_count": len(completed_sessions),
        "in_progress_count": sum(1 for s in students_data if s["status"] == "active"),
        "aggregate_statistics": {
            "average_duration_minutes": round(avg_duration, 2),
            "average_interactions": round(avg_interactions, 2),
            "average_ai_dependency": round(avg_ai_dependency, 2),
            "top_risks": [{"type": r[0], "count": r[1]} for r in top_risks],
            "cognitive_states_distribution": dict(all_states)
        },
        "students": students_data
    }

    return APIResponse(
        success=True,
        data=comparison,
        message=f"Comparativa de {len(students_data)} estudiantes en actividad {activity_id}"
    )


@router.get(
    "/alerts",
    summary="Obtener alertas en tiempo real",
    description="Obtiene alertas de estudiantes con dificultades o riesgos críticos (HU-DOC-004). Requiere rol teacher."
)
async def get_teacher_alerts(
    severity: str = Query("all", description="Filtro por severidad: all, critical, high, medium"),
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene alertas en tiempo real de estudiantes que necesitan intervención pedagógica.

    **HU-DOC-004**: Permite al docente intervenir antes de que el estudiante
    se frustre o abandone.

    **Criterios de alerta:**
    - 3+ riesgos medios
    - 1+ riesgo crítico
    - Más de 2 horas en la misma fase
    - Dependencia de IA > 85%

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/alerts
    GET /api/v1/teacher/alerts?severity=critical
    ```
    """
    # Obtener todas las sesiones activas
    active_sessions = [s for s in session_repo.get_all() if s.status == "active"]

    # FIX Cortez52: Batch load all risks and traces to avoid N+1 queries
    active_session_ids = [s.id for s in active_sessions]
    all_risks_by_session = risk_repo.get_by_session_ids(active_session_ids) if active_session_ids else {}
    all_traces_by_session = trace_repo.get_by_session_ids(active_session_ids) if active_session_ids else {}

    alerts = []

    for session in active_sessions:
        # FIX Cortez52: Use pre-loaded data instead of per-session queries
        risks = all_risks_by_session.get(session.id, [])

        # Clasificar riesgos (DB almacena en lowercase)
        critical_risks = [r for r in risks if r.risk_level == "critical"]
        high_risks = [r for r in risks if r.risk_level == "high"]
        medium_risks = [r for r in risks if r.risk_level == "medium"]

        # FIX Cortez52: Use pre-loaded traces
        traces = all_traces_by_session.get(session.id, [])

        ai_involvements = [t.ai_involvement or 0.0 for t in traces]
        ai_dependency_avg = sum(ai_involvements) / len(ai_involvements) if ai_involvements else 0.0

        # Calcular duración de la sesión
        # FIX Cortez79: Ensure start_time is timezone-aware for subtraction
        start_time_aware = _ensure_aware(session.start_time)
        duration_hours = (utc_now() - start_time_aware).total_seconds() / 3600.0 if start_time_aware else 0.0

        # Determinar si genera alerta
        alert_reasons = []
        alert_severity = "low"

        if len(critical_risks) >= 1:
            alert_reasons.append(f"{len(critical_risks)} riesgo(s) crítico(s)")
            alert_severity = "critical"

        if len(high_risks) >= 2:
            alert_reasons.append(f"{len(high_risks)} riesgos altos")
            if alert_severity == "low":
                alert_severity = "high"

        if len(medium_risks) >= 3:
            alert_reasons.append(f"{len(medium_risks)} riesgos medios")
            if alert_severity == "low":
                alert_severity = "medium"

        if ai_dependency_avg > 0.85:
            alert_reasons.append(f"Dependencia de IA muy alta ({ai_dependency_avg*100:.0f}%)")
            if alert_severity == "low":
                alert_severity = "high"

        if duration_hours > 2.0:
            alert_reasons.append(f"Sesión prolongada ({duration_hours:.1f} horas)")
            if alert_severity == "low":
                alert_severity = "medium"

        # Si hay razones para alerta, agregarla
        if alert_reasons:
            # Filtrar por severidad si se especificó
            if severity != "all" and alert_severity != severity:
                continue

            # Sugerencias de intervención
            suggestions = []
            if len(critical_risks) >= 1:
                suggestions.append("Intervención inmediata: revisar riesgos críticos con el estudiante")
            if ai_dependency_avg > 0.85:
                suggestions.append("Fomentar autonomía: reducir dependencia de IA")
            if duration_hours > 2.0:
                suggestions.append("Chequear progreso: puede estar bloqueado o perdido")

            alerts.append({
                "alert_id": f"alert_{session.id}",
                "student_id": session.student_id,
                "session_id": session.id,
                "activity_id": session.activity_id,
                "severity": alert_severity,
                "reasons": alert_reasons,
                "suggestions": suggestions,
                "metrics": {
                    "critical_risks": len(critical_risks),
                    "high_risks": len(high_risks),
                    "medium_risks": len(medium_risks),
                    "ai_dependency": round(ai_dependency_avg, 2),
                    "duration_hours": round(duration_hours, 2),
                    "total_interactions": len(traces)
                },
                "timestamp": utc_now().isoformat()
            })

    # Ordenar por severidad
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    alerts.sort(key=lambda a: severity_order[a["severity"]])

    return APIResponse(
        success=True,
        data={
            "total_alerts": len(alerts),
            "by_severity": {
                "critical": sum(1 for a in alerts if a["severity"] == "critical"),
                "high": sum(1 for a in alerts if a["severity"] == "high"),
                "medium": sum(1 for a in alerts if a["severity"] == "medium"),
            },
            "alerts": alerts
        },
        message=f"Se encontraron {len(alerts)} alertas activas"
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    summary="Marcar alerta como atendida",
    description="Marca una alerta como atendida por el docente. Requiere rol teacher."
)
async def acknowledge_alert(
    alert_id: str,
    notes: str = Query(None, description="Notas del docente sobre la intervención"),
    action_taken: str = Query(None, description="Descripción de la acción tomada"),
    db: Session = Depends(get_db),
    intervention_repo: InterventionRepository = Depends(get_intervention_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Marca una alerta como atendida y persiste la intervención.

    FIX Cortez82: Ahora persiste en tabla teacher_interventions.

    **Campos persistidos:**
    - alert_id: ID de la alerta
    - teacher_id: ID del docente
    - student_id: Extraído del alert_id (formato: alert_{session_id})
    - notes: Notas del docente
    - action_taken: Descripción de la acción
    """
    # Extraer student_id del alert_id si es posible
    # Formato: alert_{session_id}
    session_id = None
    student_id = "unknown"

    if alert_id.startswith("alert_"):
        session_id = alert_id.replace("alert_", "")

    # Crear intervención persistente
    intervention = intervention_repo.create(
        teacher_id=current_user.get("user_id"),
        student_id=student_id,
        session_id=session_id,
        alert_id=alert_id,
        intervention_type="alert_acknowledgment",
        notes=notes,
        action_taken=action_taken,
        alert_context={"original_alert_id": alert_id},
    )
    db.commit()

    return APIResponse(
        success=True,
        data={
            "intervention_id": intervention.id,
            "alert_id": alert_id,
            "acknowledged_at": intervention.created_at.isoformat() if intervention.created_at else utc_now().isoformat(),
            "teacher_id": current_user.get("user_id"),
            "notes": notes or "Sin notas",
            "action_taken": action_taken,
            "status": intervention.status,
        },
        message=f"Alerta {alert_id} marcada como atendida y registrada"
    )


@router.get(
    "/interventions",
    summary="Obtener intervenciones del docente",
    description="Lista las intervenciones realizadas por el docente. Requiere rol teacher."
)
async def get_teacher_interventions(
    status: str = Query(None, description="Filtrar por estado: acknowledged, in_progress, resolved"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    intervention_repo: InterventionRepository = Depends(get_intervention_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene las intervenciones realizadas por el docente actual.

    FIX Cortez82: Nuevo endpoint para listar intervenciones persistidas.
    """
    teacher_id = current_user.get("user_id")

    interventions = intervention_repo.get_by_teacher(
        teacher_id=teacher_id,
        status=status,
        limit=limit,
        offset=offset
    )

    total = intervention_repo.count_by_teacher(teacher_id, status)

    return APIResponse(
        success=True,
        data={
            "teacher_id": teacher_id,
            "total": total,
            "returned": len(interventions),
            "pagination": {
                "offset": offset,
                "limit": limit,
                "has_more": (offset + len(interventions)) < total
            },
            "interventions": [
                {
                    "id": i.id,
                    "alert_id": i.alert_id,
                    "student_id": i.student_id,
                    "session_id": i.session_id,
                    "intervention_type": i.intervention_type,
                    "notes": i.notes,
                    "action_taken": i.action_taken,
                    "status": i.status,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                    "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
                }
                for i in interventions
            ]
        },
        message=f"Se encontraron {total} intervenciones"
    )


@router.patch(
    "/interventions/{intervention_id}/status",
    summary="Actualizar estado de intervención",
    description="Actualiza el estado de una intervención. Requiere rol teacher."
)
async def update_intervention_status(
    intervention_id: str,
    status: str = Query(..., description="Nuevo estado: in_progress, resolved, closed"),
    resolution_notes: str = Query(None, description="Notas de resolución"),
    db: Session = Depends(get_db),
    intervention_repo: InterventionRepository = Depends(get_intervention_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Actualiza el estado de una intervención.

    FIX Cortez82: Permite al docente marcar intervenciones como resueltas.
    """
    intervention = intervention_repo.update_status(
        intervention_id=intervention_id,
        status=status,
        resolution_notes=resolution_notes
    )

    if not intervention:
        return APIResponse(
            success=False,
            data=None,
            message=f"Intervención {intervention_id} no encontrada"
        )

    db.commit()

    return APIResponse(
        success=True,
        data={
            "id": intervention.id,
            "status": intervention.status,
            "resolution_notes": intervention.resolution_notes,
            "resolved_at": intervention.resolved_at.isoformat() if intervention.resolved_at else None,
        },
        message=f"Intervención {intervention_id} actualizada a {status}"
    )


# =====================================================================
# TRACEABILITY ENDPOINTS FOR TEACHERS (Cortez63)
# =====================================================================

@router.get(
    "/students/{student_id}/traceability",
    summary="Obtener trazabilidad N4 de un estudiante",
    description="Obtiene la trazabilidad cognitiva completa de un estudiante. Requiere rol teacher."
)
async def get_student_traceability(
    student_id: str,
    activity_id: str = Query(None, description="Filtrar por actividad específica"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de trazas a retornar"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene la trazabilidad cognitiva N4 de un estudiante específico.

    **Niveles N4:**
    - N1 (Raw): Datos brutos de interacción
    - N2 (Preprocessed): Datos preprocesados con contexto
    - N3 (LLM): Análisis del modelo de IA
    - N4 (Postprocessed): Síntesis cognitiva final

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/students/student_001/traceability
    GET /api/v1/teacher/students/student_001/traceability?activity_id=prog2_tp1
    ```
    """
    # Get traces for the student
    traces = trace_repo.get_by_student_filtered(
        student_id=student_id,
        activity_id=activity_id,
        limit=limit,
        offset=offset
    )

    total_count = trace_repo.count_by_student_filtered(
        student_id=student_id,
        activity_id=activity_id
    )

    # Aggregate cognitive state distribution
    cognitive_states: Dict[str, int] = defaultdict(int)
    trace_levels: Dict[str, int] = defaultdict(int)
    interaction_types: Dict[str, int] = defaultdict(int)
    ai_involvement_values: List[float] = []

    trace_list = []
    for trace in traces:
        if trace.cognitive_state:
            cognitive_states[trace.cognitive_state] += 1
        if trace.trace_level:
            trace_levels[trace.trace_level] += 1
        if trace.interaction_type:
            interaction_types[trace.interaction_type] += 1
        if trace.ai_involvement is not None:
            ai_involvement_values.append(trace.ai_involvement)

        trace_list.append({
            "id": trace.id,
            "session_id": trace.session_id,
            "activity_id": trace.activity_id,
            "trace_level": trace.trace_level,
            "interaction_type": trace.interaction_type,
            "cognitive_state": trace.cognitive_state,
            "cognitive_intent": trace.cognitive_intent,
            "decision_justification": trace.decision_justification,
            "strategy_type": trace.strategy_type,
            "ai_involvement": trace.ai_involvement,
            "content": trace.content[:200] + "..." if trace.content and len(trace.content) > 200 else trace.content,
            "agent_id": trace.agent_id,
            "created_at": trace.created_at.isoformat() if trace.created_at else None,
        })

    # Calculate averages
    avg_ai_involvement = sum(ai_involvement_values) / len(ai_involvement_values) if ai_involvement_values else 0.0

    return APIResponse(
        success=True,
        data={
            "student_id": student_id,
            "activity_id": activity_id,
            "total_traces": total_count,
            "returned_traces": len(trace_list),
            "pagination": {
                "offset": offset,
                "limit": limit,
                "has_more": (offset + len(trace_list)) < total_count
            },
            "summary": {
                "cognitive_states_distribution": dict(cognitive_states),
                "trace_levels_distribution": dict(trace_levels),
                "interaction_types_distribution": dict(interaction_types),
                "average_ai_involvement": round(avg_ai_involvement, 2),
                "total_n4_traces": trace_levels.get("N4", 0),
            },
            "traces": trace_list
        },
        message=f"Trazabilidad de estudiante {student_id}"
    )


@router.get(
    "/students/{student_id}/cognitive-path",
    summary="Obtener camino cognitivo de un estudiante",
    description="Visualiza la evolución cognitiva del estudiante a través de sus sesiones. Requiere rol teacher."
)
async def get_student_cognitive_path(
    student_id: str,
    session_id: str = Query(None, description="Filtrar por sesión específica"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene el camino cognitivo del estudiante mostrando transiciones de estado.

    **Estados cognitivos rastreados:**
    - INICIO: Inicio de la tarea
    - EXPLORACION: Explorando el problema
    - IMPLEMENTACION: Escribiendo código
    - DEPURACION: Corrigiendo errores
    - CAMBIO_ESTRATEGIA: Cambiando de enfoque
    - VALIDACION: Verificando solución
    - ESTANCAMIENTO: Bloqueado
    - REFLEXION: Reflexión metacognitiva

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/students/student_001/cognitive-path
    GET /api/v1/teacher/students/student_001/cognitive-path?session_id=abc123
    ```
    """
    # Get traces ordered by time
    if session_id:
        traces = trace_repo.get_by_session(session_id, limit=500)
    else:
        traces = trace_repo.get_by_student(student_id, limit=500)

    if not traces:
        return APIResponse(
            success=True,
            data={
                "student_id": student_id,
                "session_id": session_id,
                "cognitive_path": [],
                "transitions": [],
                "time_in_states": {},
                "insights": []
            },
            message="No hay trazas para este estudiante"
        )

    # Build cognitive path
    cognitive_path = []
    transitions = []
    time_in_states: Dict[str, float] = defaultdict(float)
    prev_state = None
    prev_time = None

    for trace in traces:
        current_state = trace.cognitive_state
        current_time = trace.created_at

        if current_state:
            cognitive_path.append({
                "state": current_state,
                "timestamp": current_time.isoformat() if current_time else None,
                "ai_involvement": trace.ai_involvement,
                "trace_level": trace.trace_level,
                "session_id": trace.session_id,
            })

            # Track transitions
            if prev_state and prev_state != current_state:
                transitions.append({
                    "from": prev_state,
                    "to": current_state,
                    "timestamp": current_time.isoformat() if current_time else None,
                })

            # Calculate time in each state
            if prev_state and prev_time and current_time:
                duration = (current_time - prev_time).total_seconds() / 60.0  # minutes
                if duration < 120:  # Cap at 2 hours to avoid session breaks
                    time_in_states[prev_state] += duration

            prev_state = current_state
            prev_time = current_time

    # Generate insights
    insights = []
    if time_in_states:
        most_time_state = max(time_in_states.items(), key=lambda x: x[1])
        insights.append(f"Mayor tiempo en estado: {most_time_state[0]} ({most_time_state[1]:.1f} min)")

    if time_in_states.get("ESTANCAMIENTO", 0) > 10:
        insights.append("Alerta: Tiempo significativo en estado ESTANCAMIENTO")

    blocked_transitions = [t for t in transitions if t["to"] == "ESTANCAMIENTO"]
    if len(blocked_transitions) > 3:
        insights.append(f"Patrón: {len(blocked_transitions)} transiciones a ESTANCAMIENTO")

    return APIResponse(
        success=True,
        data={
            "student_id": student_id,
            "session_id": session_id,
            "total_states": len(cognitive_path),
            "unique_states": list(set(s["state"] for s in cognitive_path)),
            "cognitive_path": cognitive_path[-50:],  # Last 50 states
            "transitions": transitions[-30:],  # Last 30 transitions
            "time_in_states": {k: round(v, 2) for k, v in time_in_states.items()},
            "insights": insights
        },
        message=f"Camino cognitivo de estudiante {student_id}"
    )


@router.get(
    "/traceability/summary",
    summary="Resumen de trazabilidad de todos los estudiantes",
    description="Obtiene métricas agregadas de trazabilidad N4 para el dashboard docente. Requiere rol teacher."
)
async def get_traceability_summary(
    activity_id: str = Query(None, description="Filtrar por actividad"),
    course_id: str = Query(None, description="Filtrar por curso/materia (Cortez82)"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene métricas agregadas de trazabilidad N4 para el dashboard del docente.

    **Métricas incluidas:**
    - Distribución de estados cognitivos global
    - Estudiantes con alto/bajo uso de IA
    - Patrones de transición más comunes
    - Alertas de trazabilidad

    **FIX Cortez82:** Agregado filtro por course_id

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/traceability/summary
    GET /api/v1/teacher/traceability/summary?activity_id=prog2_tp1
    GET /api/v1/teacher/traceability/summary?course_id=prog2
    ```
    """
    # Get all sessions (optionally filtered by activity or course)
    if activity_id:
        sessions = session_repo.get_by_activity(activity_id)
    elif course_id:
        # FIX Cortez82: Filter by course_id
        sessions = session_repo.get_by_course(course_id)
    else:
        sessions = session_repo.get_all()

    if not sessions:
        return APIResponse(
            success=True,
            data={
                "total_students": 0,
                "total_traces": 0,
                "cognitive_states_global": {},
                "ai_dependency_distribution": {},
                "alerts": []
            },
            message="No hay sesiones disponibles"
        )

    # Batch load traces
    session_ids = [s.id for s in sessions]
    traces_by_session = trace_repo.get_by_session_ids(session_ids)

    # Aggregate metrics
    cognitive_states_global: Dict[str, int] = defaultdict(int)
    students_ai_high: List[str] = []  # AI > 0.7
    students_ai_medium: List[str] = []  # AI 0.4-0.7
    students_ai_low: List[str] = []  # AI < 0.4
    students_seen: set = set()
    total_traces = 0

    for session in sessions:
        traces = traces_by_session.get(session.id, [])
        total_traces += len(traces)

        if session.student_id not in students_seen:
            students_seen.add(session.student_id)

            # Calculate AI dependency for this student
            ai_values = [t.ai_involvement for t in traces if t.ai_involvement is not None]
            if ai_values:
                avg_ai = sum(ai_values) / len(ai_values)
                if avg_ai > 0.7:
                    students_ai_high.append(session.student_id)
                elif avg_ai > 0.4:
                    students_ai_medium.append(session.student_id)
                else:
                    students_ai_low.append(session.student_id)

        for trace in traces:
            if trace.cognitive_state:
                cognitive_states_global[trace.cognitive_state] += 1

    # Generate alerts based on traceability
    alerts = []
    if len(students_ai_high) > 0:
        alerts.append({
            "type": "high_ai_dependency",
            "severity": "warning",
            "message": f"{len(students_ai_high)} estudiantes con alta dependencia de IA (>70%)",
            "students": students_ai_high[:5]  # First 5
        })

    stagnation_count = cognitive_states_global.get("ESTANCAMIENTO", 0)
    if stagnation_count > 10:
        alerts.append({
            "type": "high_stagnation",
            "severity": "warning",
            "message": f"{stagnation_count} eventos de estancamiento detectados",
        })

    return APIResponse(
        success=True,
        data={
            "activity_id": activity_id,
            "total_students": len(students_seen),
            "total_traces": total_traces,
            "cognitive_states_global": dict(cognitive_states_global),
            "ai_dependency_distribution": {
                "high": len(students_ai_high),
                "medium": len(students_ai_medium),
                "low": len(students_ai_low)
            },
            "students_by_ai_dependency": {
                "high": students_ai_high,
                "medium": students_ai_medium,
                "low": students_ai_low
            },
            "alerts": alerts
        },
        message="Resumen de trazabilidad N4"
    )


# =====================================================================
# EXPORT ENDPOINTS (Cortez82 - Mejora 4.5)
# =====================================================================


@router.get(
    "/students/{student_id}/export",
    summary="Exportar trazabilidad de un estudiante",
    description="Exporta la trazabilidad cognitiva de un estudiante en formato JSON o CSV. Requiere rol teacher."
)
async def export_student_traceability(
    student_id: str,
    format: str = Query("json", description="Formato de exportación: json o csv"),
    activity_id: str = Query(None, description="Filtrar por actividad"),
    include_risks: bool = Query(True, description="Incluir riesgos detectados"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    current_user: dict = Depends(require_teacher_role),
):
    """
    Exporta la trazabilidad cognitiva completa de un estudiante.

    FIX Cortez82: Nuevo endpoint para exportación de datos.

    **Formatos soportados:**
    - json: Estructura completa con metadatos
    - csv: Formato tabular para análisis externo

    **Ejemplo:**
    ```bash
    GET /api/v1/teacher/students/student_001/export?format=json
    GET /api/v1/teacher/students/student_001/export?format=csv&activity_id=prog2_tp1
    ```
    """
    from fastapi.responses import Response
    import csv
    import io
    import json as json_lib

    # Get traces
    traces = trace_repo.get_by_student_filtered(
        student_id=student_id,
        activity_id=activity_id,
        limit=1000  # Higher limit for export
    )

    # Get risks if requested
    risks_data = []
    if include_risks:
        risks = risk_repo.get_by_student(student_id)
        if activity_id:
            risks = [r for r in risks if r.activity_id == activity_id]
        risks_data = [
            {
                "id": r.id,
                "risk_type": r.risk_type,
                "risk_level": r.risk_level,
                "dimension": r.dimension,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in risks
        ]

    # Get sessions
    sessions = session_repo.get_by_student(student_id)
    if activity_id:
        sessions = [s for s in sessions if s.activity_id == activity_id]

    if format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "trace_id", "session_id", "activity_id", "timestamp",
            "trace_level", "interaction_type", "cognitive_state",
            "ai_involvement", "content_preview"
        ])

        # Data rows
        for trace in traces:
            writer.writerow([
                trace.id,
                trace.session_id,
                trace.activity_id,
                trace.created_at.isoformat() if trace.created_at else "",
                trace.trace_level,
                trace.interaction_type,
                trace.cognitive_state or "",
                trace.ai_involvement if trace.ai_involvement else "",
                (trace.content[:100] + "...") if trace.content and len(trace.content) > 100 else (trace.content or "")
            ])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=traceability_{student_id}.csv"
            }
        )

    else:
        # Generate JSON
        export_data = {
            "student_id": student_id,
            "activity_id": activity_id,
            "exported_at": utc_now().isoformat(),
            "exported_by": current_user.get("email"),
            "summary": {
                "total_traces": len(traces),
                "total_sessions": len(sessions),
                "total_risks": len(risks_data),
            },
            "sessions": [
                {
                    "id": s.id,
                    "activity_id": s.activity_id,
                    "mode": s.mode,
                    "status": s.status,
                    "start_time": s.start_time.isoformat() if s.start_time else None,
                    "end_time": s.end_time.isoformat() if s.end_time else None,
                    "cognitive_status": s.cognitive_status,
                    "session_metrics": s.session_metrics,
                }
                for s in sessions
            ],
            "traces": [
                {
                    "id": t.id,
                    "session_id": t.session_id,
                    "activity_id": t.activity_id,
                    "trace_level": t.trace_level,
                    "interaction_type": t.interaction_type,
                    "cognitive_state": t.cognitive_state,
                    "ai_involvement": t.ai_involvement,
                    "content": t.content,
                    "context": t.context,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                }
                for t in traces
            ],
            "risks": risks_data,
        }

        json_content = json_lib.dumps(export_data, indent=2, ensure_ascii=False)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=traceability_{student_id}.json"
            }
        )


@router.get(
    "/traceability/export",
    summary="Exportar trazabilidad por actividad",
    description="Exporta la trazabilidad de todos los estudiantes en una actividad. Requiere rol teacher."
)
async def export_activity_traceability(
    activity_id: str = Query(..., description="ID de la actividad"),
    format: str = Query("json", description="Formato: json o csv"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    current_user: dict = Depends(require_teacher_role),
):
    """
    Exporta la trazabilidad de todos los estudiantes en una actividad.

    FIX Cortez82: Nuevo endpoint para exportación masiva.
    """
    from fastapi.responses import Response
    import csv
    import io
    import json as json_lib

    # Get all sessions for the activity
    sessions = session_repo.get_by_activity(activity_id, limit=500)
    session_ids = [s.id for s in sessions]

    # Batch load traces
    traces_by_session = trace_repo.get_by_session_ids(session_ids)

    # Flatten traces
    all_traces = []
    for session_id, traces in traces_by_session.items():
        all_traces.extend(traces)

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "student_id", "session_id", "trace_id", "timestamp",
            "trace_level", "interaction_type", "cognitive_state",
            "ai_involvement"
        ])

        for trace in all_traces:
            writer.writerow([
                trace.student_id,
                trace.session_id,
                trace.id,
                trace.created_at.isoformat() if trace.created_at else "",
                trace.trace_level,
                trace.interaction_type,
                trace.cognitive_state or "",
                trace.ai_involvement if trace.ai_involvement else ""
            ])

        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=activity_{activity_id}_traceability.csv"
            }
        )

    else:
        export_data = {
            "activity_id": activity_id,
            "exported_at": utc_now().isoformat(),
            "exported_by": current_user.get("email"),
            "summary": {
                "total_sessions": len(sessions),
                "total_traces": len(all_traces),
                "unique_students": len(set(s.student_id for s in sessions)),
            },
            "sessions": [
                {
                    "id": s.id,
                    "student_id": s.student_id,
                    "status": s.status,
                    "trace_count": len(traces_by_session.get(s.id, [])),
                }
                for s in sessions
            ],
        }

        return Response(
            content=json_lib.dumps(export_data, indent=2, ensure_ascii=False),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=activity_{activity_id}_traceability.json"
            }
        )


# =====================================================================
# LONGITUDINAL METRICS (Cortez82 - Mejora 4.9)
# =====================================================================


@router.get(
    "/students/{student_id}/trends",
    summary="Métricas longitudinales de un estudiante",
    description="Obtiene la evolución temporal de métricas cognitivas. Requiere rol teacher."
)
async def get_student_trends(
    student_id: str,
    period: str = Query("month", description="Periodo: week, month, semester"),
    db: Session = Depends(get_db),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    current_user: dict = Depends(require_teacher_role),
) -> APIResponse[Dict[str, Any]]:
    """
    Obtiene métricas longitudinales para analizar progreso del estudiante.

    FIX Cortez82: Nuevo endpoint para análisis de tendencias.

    **Periodos disponibles:**
    - week: Últimos 7 días
    - month: Últimos 30 días (default)
    - semester: Últimos 120 días

    **Métricas incluidas:**
    - Evolución de dependencia IA
    - Tiempo en estados cognitivos por semana
    - Cantidad de riesgos detectados
    - Score de proceso calculado
    """
    from datetime import timedelta
    from sqlalchemy import and_

    # Determine date range
    days_map = {"week": 7, "month": 30, "semester": 120}
    days = days_map.get(period, 30)
    start_date = utc_now() - timedelta(days=days)

    # Get sessions in period
    sessions = session_repo.get_by_student(student_id, limit=500)
    sessions_in_period = [
        s for s in sessions
        if s.created_at and s.created_at >= start_date
    ]

    if not sessions_in_period:
        return APIResponse(
            success=True,
            data={
                "student_id": student_id,
                "period": period,
                "data_points": [],
                "summary": {
                    "total_sessions": 0,
                    "avg_ai_dependency": 0,
                    "trend_direction": "neutral",
                    "process_score": 0,
                }
            },
            message="No hay datos en el periodo seleccionado"
        )

    # Get traces for these sessions
    session_ids = [s.id for s in sessions_in_period]
    traces_by_session = trace_repo.get_by_session_ids(session_ids)

    # Get risks
    all_risks = risk_repo.get_by_student(student_id)
    risks_in_period = [
        r for r in all_risks
        if r.created_at and r.created_at >= start_date
    ]

    # Group data by week
    from collections import defaultdict
    weekly_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "sessions": 0,
        "traces": 0,
        "ai_involvement_sum": 0.0,
        "ai_involvement_count": 0,
        "cognitive_states": defaultdict(int),
        "risks": 0,
    })

    for session in sessions_in_period:
        # Determine week key
        week_start = session.created_at - timedelta(days=session.created_at.weekday())
        week_key = week_start.strftime("%Y-%W")

        weekly_data[week_key]["sessions"] += 1

        # Get traces for this session
        session_traces = traces_by_session.get(session.id, [])
        weekly_data[week_key]["traces"] += len(session_traces)

        for trace in session_traces:
            if trace.ai_involvement is not None:
                weekly_data[week_key]["ai_involvement_sum"] += trace.ai_involvement
                weekly_data[week_key]["ai_involvement_count"] += 1
            if trace.cognitive_state:
                weekly_data[week_key]["cognitive_states"][trace.cognitive_state] += 1

    # Count risks per week
    for risk in risks_in_period:
        week_start = risk.created_at - timedelta(days=risk.created_at.weekday())
        week_key = week_start.strftime("%Y-%W")
        if week_key in weekly_data:
            weekly_data[week_key]["risks"] += 1

    # Convert to data points
    data_points = []
    sorted_weeks = sorted(weekly_data.keys())

    for week_key in sorted_weeks:
        week_data = weekly_data[week_key]
        avg_ai = (
            week_data["ai_involvement_sum"] / week_data["ai_involvement_count"]
            if week_data["ai_involvement_count"] > 0 else 0
        )

        data_points.append({
            "week": week_key,
            "sessions": week_data["sessions"],
            "traces": week_data["traces"],
            "avg_ai_dependency": round(avg_ai, 3),
            "cognitive_states": dict(week_data["cognitive_states"]),
            "risks_detected": week_data["risks"],
        })

    # Calculate overall trend
    if len(data_points) >= 2:
        first_half = data_points[:len(data_points)//2]
        second_half = data_points[len(data_points)//2:]

        first_avg = sum(d["avg_ai_dependency"] for d in first_half) / len(first_half)
        second_avg = sum(d["avg_ai_dependency"] for d in second_half) / len(second_half)

        if second_avg < first_avg - 0.05:
            trend = "improving"
        elif second_avg > first_avg + 0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"

    # Calculate process score (Mejora 4.10)
    process_score = calculate_process_score(
        sessions=sessions_in_period,
        traces_by_session=traces_by_session,
        risks=risks_in_period
    )

    return APIResponse(
        success=True,
        data={
            "student_id": student_id,
            "period": period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": utc_now().isoformat(),
            },
            "data_points": data_points,
            "summary": {
                "total_sessions": len(sessions_in_period),
                "total_traces": sum(d["traces"] for d in data_points),
                "total_risks": len(risks_in_period),
                "avg_ai_dependency": round(
                    sum(d["avg_ai_dependency"] for d in data_points) / len(data_points)
                    if data_points else 0,
                    3
                ),
                "trend_direction": trend,
                "process_score": process_score,
            }
        },
        message=f"Tendencias de {period} para estudiante {student_id}"
    )


def calculate_process_score(
    sessions: list,
    traces_by_session: dict,
    risks: list
) -> dict:
    """
    Calculate process-based evaluation score.

    FIX Cortez82: Implementación de score de proceso (Mejora 4.10)

    Components:
    - Autonomy (40%): Based on AI dependency (lower is better)
    - Diversity (20%): Variety of cognitive states visited
    - Persistence (20%): Ability to recover from stagnation
    - Risk Avoidance (20%): Fewer risks detected

    Returns:
        dict with overall_score (0-100) and component breakdown
    """
    if not sessions:
        return {
            "overall_score": 0,
            "components": {
                "autonomy": 0,
                "diversity": 0,
                "persistence": 0,
                "risk_avoidance": 0,
            },
            "interpretation": "Sin datos suficientes"
        }

    # Collect all traces
    all_traces = []
    for session_id, traces in traces_by_session.items():
        all_traces.extend(traces)

    if not all_traces:
        return {
            "overall_score": 0,
            "components": {
                "autonomy": 0,
                "diversity": 0,
                "persistence": 0,
                "risk_avoidance": 0,
            },
            "interpretation": "Sin trazas registradas"
        }

    # 1. Autonomy Score (40%)
    ai_values = [t.ai_involvement for t in all_traces if t.ai_involvement is not None]
    if ai_values:
        avg_ai = sum(ai_values) / len(ai_values)
        # Score: 100 at 0% AI, 0 at 100% AI
        autonomy_score = max(0, min(100, (1 - avg_ai) * 100))
    else:
        autonomy_score = 50  # Neutral if no data

    # 2. Diversity Score (20%)
    cognitive_states = set(t.cognitive_state for t in all_traces if t.cognitive_state)
    # Max expected states: 8 (all defined states)
    diversity_score = min(100, (len(cognitive_states) / 8) * 100)

    # 3. Persistence Score (20%)
    # Measure ability to recover from stagnation
    state_sequence = [t.cognitive_state for t in all_traces if t.cognitive_state]
    stagnation_count = state_sequence.count("ESTANCAMIENTO")
    total_states = len(state_sequence)

    if total_states > 0:
        stagnation_ratio = stagnation_count / total_states
        # Lower stagnation = higher score
        persistence_score = max(0, min(100, (1 - stagnation_ratio * 2) * 100))
    else:
        persistence_score = 50

    # 4. Risk Avoidance Score (20%)
    # Based on risks per session
    risks_per_session = len(risks) / len(sessions) if sessions else 0
    # 0 risks = 100, 3+ risks per session = 0
    risk_avoidance_score = max(0, min(100, (1 - risks_per_session / 3) * 100))

    # Calculate weighted overall score
    overall_score = (
        autonomy_score * 0.4 +
        diversity_score * 0.2 +
        persistence_score * 0.2 +
        risk_avoidance_score * 0.2
    )

    # Interpretation
    if overall_score >= 80:
        interpretation = "Excelente proceso cognitivo con alta autonomia"
    elif overall_score >= 60:
        interpretation = "Buen proceso con areas de mejora identificables"
    elif overall_score >= 40:
        interpretation = "Proceso en desarrollo, requiere acompanamiento"
    else:
        interpretation = "Proceso con dificultades significativas"

    return {
        "overall_score": round(overall_score, 1),
        "components": {
            "autonomy": round(autonomy_score, 1),
            "diversity": round(diversity_score, 1),
            "persistence": round(persistence_score, 1),
            "risk_avoidance": round(risk_avoidance_score, 1),
        },
        "interpretation": interpretation,
        "weights": {
            "autonomy": "40%",
            "diversity": "20%",
            "persistence": "20%",
            "risk_avoidance": "20%",
        }
    }