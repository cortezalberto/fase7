"""
Router para camino cognitivo reconstructivo

Sprint 3 - HU-EST-006
FIX Cortez54: Fixed datetime naive vs aware comparison error
"""
from fastapi import APIRouter, Depends, Query  # Cortez58: Removed unused HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from collections import defaultdict
from datetime import datetime, timezone

from backend.core.constants import utc_now


def _ensure_aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    FIX Cortez54: Ensure datetime is timezone-aware (UTC).

    Handles comparison between naive (from DB) and aware (from utc_now()) datetimes.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Assume UTC for naive datetimes from database
        return dt.replace(tzinfo=timezone.utc)
    return dt

from ..deps import get_db, get_session_repository, get_trace_repository, get_risk_repository, get_current_user
from ..schemas.common import APIResponse, validate_uuid_format
from ..exceptions import SessionNotFoundError, TraceNotFoundError
from ..schemas.cognitive_path import (
    CognitivePath,
    CognitivePhase,
    CognitiveTransition,
    CognitivePathSummary,
    AIDependencyPoint,
)
from ...database.repositories import SessionRepository, TraceRepository, RiskRepository

router = APIRouter(prefix="/cognitive-path", tags=["Cognitive Path"])


@router.get(
    "/{session_id}",
    response_model=APIResponse[CognitivePath],
    summary="Obtener camino cognitivo",
    description="Reconstruye el camino cognitivo completo de un estudiante en una sesión (HU-EST-006)"
)
async def get_cognitive_path(
    session_id: str,
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    _current_user: dict = Depends(get_current_user),  # FIX Cortez20: Add auth
) -> APIResponse[CognitivePath]:
    """
    Reconstruye y visualiza el camino cognitivo completo de un estudiante.

    **HU-EST-006**: Permite al estudiante ver su trayectoria de razonamiento
    para reflexionar sobre su proceso (metacognición).

    **Información incluida:**
    - Secuencia de estados cognitivos atravesados
    - Transiciones entre estados con timestamps
    - Puntos donde solicitó ayuda
    - Riesgos detectados en cada fase
    - Evolución de dependencia de IA (0-100%)
    - Métricas de resumen

    **Ejemplo de uso:**
    ```bash
    GET /api/v1/cognitive-path/session_abc123
    ```
    """
    # FIX Cortez33: Validate UUID format before DB access
    session_id = validate_uuid_format(session_id, "session_id")

    # FIX Cortez33: Use custom exceptions for consistent error handling
    # Validar sesión
    db_session = session_repo.get_by_id(session_id)
    if not db_session:
        raise SessionNotFoundError(session_id)

    # Obtener todas las trazas de la sesión
    traces = trace_repo.get_by_session(session_id)
    if not traces:
        raise TraceNotFoundError(session_id=session_id)

    # Obtener riesgos de la sesión
    risks = risk_repo.get_by_session(session_id)

    # Reconstruir fases cognitivas
    phases_dict = defaultdict(list)
    transitions = []
    prev_state = None
    blocked_count = 0

    for trace in sorted(traces, key=lambda t: t.created_at):
        state = trace.cognitive_state or "unknown"

        # Agrupar por estado cognitivo
        phases_dict[state].append(trace)

        # Detectar transiciones
        # FIX Cortez56: Ensure transition timestamps are timezone-aware
        if prev_state and prev_state != state:
            transitions.append(
                CognitiveTransition(
                    from_phase=prev_state,
                    to_phase=state,
                    timestamp=_ensure_aware(trace.created_at),
                    trigger=trace.cognitive_intent or "Cambio de fase"
                )
            )
        prev_state = state

        # Contar bloqueados
        if trace.trace_metadata and trace.trace_metadata.get("blocked"):
            blocked_count += 1

    # Construir fases detalladas
    phases = []
    for phase_name, phase_traces in phases_dict.items():
        if not phase_traces:
            continue

        # FIX Cortez56: Ensure all trace timestamps are timezone-aware for comparison
        start_time = _ensure_aware(min(t.created_at for t in phase_traces))
        end_time = _ensure_aware(max(t.created_at for t in phase_traces))
        duration = (end_time - start_time).total_seconds() / 60.0

        # Calcular promedio de AI involvement
        ai_involvements = [t.ai_involvement or 0.0 for t in phase_traces]
        ai_avg = sum(ai_involvements) / len(ai_involvements) if ai_involvements else 0.0

        # Riesgos en esta fase
        phase_risks = [
            r.risk_type
            for r in risks
            if any(t.id in (r.trace_ids or []) for t in phase_traces)
        ]

        # Decisiones clave (de justificaciones)
        key_decisions = [
            t.decision_justification
            for t in phase_traces
            if t.decision_justification
        ]

        phases.append(
            CognitivePhase(
                phase_name=phase_name,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=round(duration, 2),
                interactions_count=len(phase_traces),
                ai_involvement_avg=round(ai_avg, 2),
                risks_detected=phase_risks,
                key_decisions=key_decisions[:3]  # Top 3
            )
        )

    # Ordenar fases por tiempo
    phases.sort(key=lambda p: p.start_time)

    # Calcular resumen
    # FIX Cortez54: Use _ensure_aware to handle naive vs aware datetime comparison
    start_time_aware = _ensure_aware(db_session.start_time)
    end_time_aware = _ensure_aware(db_session.end_time)
    total_duration = (
        (end_time_aware - start_time_aware).total_seconds() / 60.0
        if end_time_aware
        else (utc_now() - start_time_aware).total_seconds() / 60.0
    )

    all_ai_involvements = [t.ai_involvement or 0.0 for t in traces]
    ai_dependency_avg = sum(all_ai_involvements) / len(all_ai_involvements) if all_ai_involvements else 0.0

    # Contar cambios de estrategia (en metadata)
    strategy_changes_count = sum(
        1 for t in traces
        if t.trace_metadata and t.trace_metadata.get("strategy_change")
    )

    # Extraer lista de cambios de estrategia con descripciones
    strategy_changes_list = [
        t.trace_metadata.get("strategy_change_description", f"Cambio de estrategia en {t.cognitive_state}")
        for t in sorted(traces, key=lambda x: x.created_at)
        if t.trace_metadata and t.trace_metadata.get("strategy_change")
    ]

    # Construir evolución de dependencia de IA (series temporales)
    # FIX Cortez56: Ensure AI dependency timestamps are timezone-aware
    ai_dependency_evolution = [
        AIDependencyPoint(
            timestamp=_ensure_aware(t.created_at),
            ai_involvement=t.ai_involvement or 0.0
        )
        for t in sorted(traces, key=lambda x: x.created_at)
    ]

    # Agrupar riesgos por nivel
    risks_by_level = defaultdict(int)
    for risk in risks:
        risks_by_level[risk.risk_level] += 1

    summary = CognitivePathSummary(
        total_interactions=len(traces),
        total_duration_minutes=round(total_duration, 2),
        blocked_interactions=blocked_count,
        ai_dependency_average=round(ai_dependency_avg, 2),
        strategy_changes=strategy_changes_count,
        risks_total=len(risks),
        risks_by_level=dict(risks_by_level)
    )

    # Construir respuesta
    # FIX Cortez56: Ensure session timestamps are timezone-aware
    cognitive_path = CognitivePath(
        session_id=session_id,
        student_id=db_session.student_id,
        activity_id=db_session.activity_id,
        start_time=_ensure_aware(db_session.start_time),
        end_time=_ensure_aware(db_session.end_time),
        summary=summary,
        phases=phases,
        transitions=transitions,
        ai_dependency_evolution=ai_dependency_evolution,
        strategy_changes=strategy_changes_list,
    )

    return APIResponse(
        success=True,
        data=cognitive_path,
        message=f"Camino cognitivo reconstructivo de sesión {session_id}"
    )


@router.get(
    "/{session_id}/summary",
    response_model=APIResponse[CognitivePathSummary],
    summary="Obtener resumen del camino cognitivo",
    description="Obtiene solo el resumen cuantitativo del camino cognitivo"
)
async def get_cognitive_path_summary(
    session_id: str,
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    risk_repo: RiskRepository = Depends(get_risk_repository),
    _current_user: dict = Depends(get_current_user),  # FIX Cortez22 DEFECTO 2.2: Require auth
) -> APIResponse[CognitivePathSummary]:
    """
    Obtiene solo las métricas resumen del camino cognitivo sin el detalle de fases.

    **Útil para:**
    - Dashboards con muchos estudiantes
    - Comparaciones rápidas
    - Visualizaciones agregadas
    """
    # FIX Cortez33: Validate UUID format before DB access
    session_id = validate_uuid_format(session_id, "session_id")

    # FIX Cortez33: Use custom exceptions for consistent error handling
    # Validar sesión
    db_session = session_repo.get_by_id(session_id)
    if not db_session:
        raise SessionNotFoundError(session_id)

    # Obtener trazas y riesgos
    traces = trace_repo.get_by_session(session_id)
    risks = risk_repo.get_by_session(session_id)

    if not traces:
        # Sesión sin trazas
        summary = CognitivePathSummary(
            total_interactions=0,
            total_duration_minutes=0.0,
            blocked_interactions=0,
            ai_dependency_average=0.0,
            strategy_changes=0,
            risks_total=0,
            risks_by_level={}
        )
        return APIResponse(
            success=True,
            data=summary,
            message=f"Resumen de sesión {session_id} (sin trazas)"
        )

    # Calcular métricas
    blocked_count = sum(
        1 for t in traces
        if t.trace_metadata and t.trace_metadata.get("blocked")
    )

    all_ai_involvements = [t.ai_involvement or 0.0 for t in traces]
    ai_dependency_avg = sum(all_ai_involvements) / len(all_ai_involvements)

    strategy_changes = sum(
        1 for t in traces
        if t.trace_metadata and t.trace_metadata.get("strategy_change")
    )

    # FIX Cortez54: Use _ensure_aware to handle naive vs aware datetime comparison
    start_aware = _ensure_aware(db_session.start_time)
    end_aware = _ensure_aware(db_session.end_time)
    total_duration = (
        (end_aware - start_aware).total_seconds() / 60.0
        if end_aware
        else (utc_now() - start_aware).total_seconds() / 60.0
    )

    risks_by_level = defaultdict(int)
    for risk in risks:
        risks_by_level[risk.risk_level] += 1

    summary = CognitivePathSummary(
        total_interactions=len(traces),
        total_duration_minutes=round(total_duration, 2),
        blocked_interactions=blocked_count,
        ai_dependency_average=round(ai_dependency_avg, 2),
        strategy_changes=strategy_changes,
        risks_total=len(risks),
        risks_by_level=dict(risks_by_level)
    )

    return APIResponse(
        success=True,
        data=summary,
        message=f"Resumen de camino cognitivo de sesión {session_id}"
    )