"""
Incident Simulator Endpoints (IR-IA) - Incident Response Simulation.

Cortez46: Extracted from monolithic simulators.py (1,589 lines)
FIX Cortez52: Migrated HTTPExceptions to custom exceptions

Contains:
- POST /incident/start: Start incident simulation
- POST /incident/diagnose: Add diagnosis step
- POST /incident/resolve: Resolve incident with evaluation
- GET /incident/{incident_id}: Get incident details

Sprint 6 - HU-EST-012
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ...deps import get_db, get_current_user
from ...schemas.common import APIResponse
from ...schemas.simulators import (
    IncidentStartRequest,
    DiagnosisStepRequest,
    IncidentSolutionRequest,
    IncidentResponse,
)
from ...exceptions import (
    SessionNotFoundError,
    IncidentNotFoundError,
    DatabaseOperationError,
)
from ....agents.simulators import SimuladorProfesionalAgent, SimuladorType
from ....database.repositories import SessionRepository, IncidentSimulationRepository
from ....llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Incident Simulator (IR-IA)"])


@router.post(
    "/incident/start",
    response_model=APIResponse[IncidentResponse],
    summary="Start Incident Simulation (Sprint 6)",
    description="Inicia una simulación de incidente en producción con IR-IA",
)
async def start_incident(
    request: IncidentStartRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[IncidentResponse]:
    """
    Inicia una simulación de respuesta a incidentes (SPRINT 6).

    El agente IR-IA generará:
    - Descripción realista del incidente
    - Logs simulados del sistema
    - Métricas simuladas (CPU, memory, requests, errors)
    """
    try:
        # Validate session
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Initialize simulator
        # FIX Cortez54: Added required simulator_type argument
        llm_provider = LLMProviderFactory.create_from_env()
        simulator = SimuladorProfesionalAgent(
            simulator_type=SimuladorType.INCIDENT_RESPONDER,
            llm_provider=llm_provider
        )

        # Generate incident scenario
        incident_scenario = await simulator.generar_incidente(
            tipo_incidente=request.incident_type,
            severidad=request.severity,
        )

        # Create incident simulation
        incident_repo = IncidentSimulationRepository(db)
        incident = incident_repo.create(
            session_id=request.session_id,
            student_id=request.student_id,
            incident_type=request.incident_type,
            activity_id=request.activity_id,
            severity=request.severity,
            incident_description=incident_scenario.get("description", ""),
            simulated_logs=incident_scenario.get("logs", ""),
            simulated_metrics=incident_scenario.get("metrics", {}),
        )

        logger.info(
            "Incident simulation started",
            extra={
                "incident_id": incident.id,
                "incident_type": request.incident_type,
                "severity": request.severity,
            },
        )

        return APIResponse(
            success=True,
            data=IncidentResponse(
                incident_id=incident.id,
                session_id=incident.session_id,
                student_id=incident.student_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                incident_description=incident.incident_description,
                simulated_logs=incident.simulated_logs,
                simulated_metrics=incident.simulated_metrics,
                diagnosis_process=incident.diagnosis_process,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
            ),
            message="Incident simulation started successfully",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error("Error starting incident simulation", exc_info=True)
        raise DatabaseOperationError("start_incident", details=str(e))


@router.post(
    "/incident/diagnose",
    response_model=APIResponse[IncidentResponse],
    summary="Add Diagnosis Step (Sprint 6)",
    description="Agrega un paso de diagnóstico al proceso de resolución",
)
async def add_diagnosis_step(
    request: DiagnosisStepRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[IncidentResponse]:
    """
    Registra un paso en el proceso de diagnóstico del incidente (SPRINT 6).

    Captura:
    - Acción tomada (ej: "Revisar logs de la API")
    - Hallazgo (ej: "Error 500 en endpoint /users")
    """
    try:
        incident_repo = IncidentSimulationRepository(db)
        incident = incident_repo.get_by_id(request.incident_id)

        if not incident:
            raise IncidentNotFoundError(request.incident_id)

        # Add diagnosis step
        diagnosis_step = {
            "action": request.action,
            "finding": request.finding,
            "timestamp": incident.updated_at.isoformat(),
        }
        incident = incident_repo.add_diagnosis_step(incident.id, diagnosis_step)

        logger.info(
            "Diagnosis step added",
            extra={
                "incident_id": incident.id,
                "step_count": len(incident.diagnosis_process),
            },
        )

        return APIResponse(
            success=True,
            data=IncidentResponse(
                incident_id=incident.id,
                session_id=incident.session_id,
                student_id=incident.student_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                incident_description=incident.incident_description,
                simulated_logs=incident.simulated_logs,
                simulated_metrics=incident.simulated_metrics,
                diagnosis_process=incident.diagnosis_process,
                solution_proposed=incident.solution_proposed,
                root_cause_identified=incident.root_cause_identified,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
            ),
            message="Diagnosis step added successfully",
        )

    except IncidentNotFoundError:
        raise
    except Exception as e:
        logger.error("Error adding diagnosis step", exc_info=True)
        raise DatabaseOperationError("add_diagnosis_step", details=str(e))


@router.post(
    "/incident/resolve",
    response_model=APIResponse[IncidentResponse],
    summary="Resolve Incident (Sprint 6)",
    description="Envía solución propuesta y finaliza el incidente",
)
async def resolve_incident(
    request: IncidentSolutionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[IncidentResponse]:
    """
    Completa la resolución del incidente (SPRINT 6).

    El agente IR-IA evaluará:
    - Sistematización del diagnóstico
    - Priorización correcta
    - Calidad de la documentación post-mortem
    - Comunicación clara
    """
    try:
        incident_repo = IncidentSimulationRepository(db)
        incident = incident_repo.get_by_id(request.incident_id)

        if not incident:
            raise IncidentNotFoundError(request.incident_id)

        # Evaluate resolution with IR-IA
        # FIX Cortez54: Added required simulator_type argument
        llm_provider = LLMProviderFactory.create_from_env()
        simulator = SimuladorProfesionalAgent(
            simulator_type=SimuladorType.INCIDENT_RESPONDER,
            llm_provider=llm_provider
        )

        evaluation = await simulator.evaluar_resolucion_incidente(
            proceso_diagnostico=incident.diagnosis_process,
            solucion=request.solution_proposed,
            causa_raiz=request.root_cause_identified,
            post_mortem=request.post_mortem,
        )

        # Calculate time metrics
        time_to_diagnose = len(incident.diagnosis_process) * 5  # Estimate 5 min per step
        time_to_resolve = int(
            (incident.updated_at - incident.created_at).total_seconds() / 60
        )

        # Complete incident
        incident = incident_repo.complete_incident(
            incident_id=incident.id,
            solution_proposed=request.solution_proposed,
            root_cause_identified=request.root_cause_identified,
            post_mortem=request.post_mortem,
            time_to_diagnose_minutes=time_to_diagnose,
            time_to_resolve_minutes=time_to_resolve,
            evaluation=evaluation,
        )

        logger.info(
            "Incident resolved",
            extra={
                "incident_id": incident.id,
                "time_to_resolve": time_to_resolve,
                "evaluation_score": evaluation.get("overall_score", 0.0),
            },
        )

        return APIResponse(
            success=True,
            data=IncidentResponse(
                incident_id=incident.id,
                session_id=incident.session_id,
                student_id=incident.student_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                incident_description=incident.incident_description,
                simulated_logs=incident.simulated_logs,
                simulated_metrics=incident.simulated_metrics,
                diagnosis_process=incident.diagnosis_process,
                solution_proposed=incident.solution_proposed,
                root_cause_identified=incident.root_cause_identified,
                time_to_diagnose_minutes=incident.time_to_diagnose_minutes,
                time_to_resolve_minutes=incident.time_to_resolve_minutes,
                post_mortem=incident.post_mortem,
                evaluation=incident.evaluation,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
            ),
            message="Incident resolved successfully",
        )

    except IncidentNotFoundError:
        raise
    except Exception as e:
        logger.error("Error resolving incident", exc_info=True)
        raise DatabaseOperationError("resolve_incident", details=str(e))


@router.get(
    "/incident/{incident_id}",
    response_model=APIResponse[IncidentResponse],
    summary="Get Incident Details (Sprint 6)",
    description="Obtiene detalles completos de una simulación de incidente",
)
async def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[IncidentResponse]:
    """Obtiene detalles completos de un incidente simulado (SPRINT 6)"""
    try:
        incident_repo = IncidentSimulationRepository(db)
        incident = incident_repo.get_by_id(incident_id)

        if not incident:
            raise IncidentNotFoundError(incident_id)

        return APIResponse(
            success=True,
            data=IncidentResponse(
                incident_id=incident.id,
                session_id=incident.session_id,
                student_id=incident.student_id,
                incident_type=incident.incident_type,
                severity=incident.severity,
                incident_description=incident.incident_description,
                simulated_logs=incident.simulated_logs,
                simulated_metrics=incident.simulated_metrics,
                diagnosis_process=incident.diagnosis_process,
                solution_proposed=incident.solution_proposed,
                root_cause_identified=incident.root_cause_identified,
                time_to_diagnose_minutes=incident.time_to_diagnose_minutes,
                time_to_resolve_minutes=incident.time_to_resolve_minutes,
                post_mortem=incident.post_mortem,
                evaluation=incident.evaluation,
                created_at=incident.created_at,
                updated_at=incident.updated_at,
            ),
        )

    except IncidentNotFoundError:
        raise
    except Exception as e:
        logger.error("Error retrieving incident", exc_info=True)
        raise DatabaseOperationError("retrieve_incident", details=str(e))
