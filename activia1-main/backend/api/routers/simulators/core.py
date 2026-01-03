"""
Core Simulator Endpoints - List, interact, and get simulator info.

Cortez46: Extracted from monolithic simulators.py (1,589 lines)
FIX Cortez52: Migrated HTTPExceptions to custom exceptions

Contains:
- GET /simulators: List all available simulators
- POST /simulators/interact: Interact with a simulator
- GET /simulators/{simulator_type}: Get simulator info

Sprint 3 - HU-EST-009, HU-SYS-006
"""
from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import time
from uuid import uuid4

from ...deps import (
    get_db,
    get_session_repository,
    get_trace_repository,
    get_llm_provider,
    get_current_user,
)
from ...schemas.common import APIResponse
from ...schemas.simulator import (
    SimulatorInteractionRequest,
    SimulatorInteractionResponse,
    SimulatorInfoResponse,
    SimulatorType,
)
from ...exceptions import (
    SessionNotFoundError,
    SessionInactiveError,
    SimulatorNotSupportedError,
    SimulatorCreationError,
    SimulatorInteractionError,
    EmptyPromptError,
    ValidationError,
    DatabaseOperationError,
)
from ....agents.simulators import (
    SimuladorProfesionalAgent,
    SimuladorType as AgentSimulatorType,
)
from ....database.repositories import SessionRepository, TraceRepository
from ....models.trace import CognitiveTrace, TraceLevel, InteractionType
from ....llm.base import LLMProvider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulators", tags=["Simulators"])


# Import and include sub-routers
from .interview import router as interview_router
from .incident import router as incident_router
# Cortez66: Renamed from sprint6.py to advanced.py
from .advanced import router as advanced_router

router.include_router(interview_router)
router.include_router(incident_router)
router.include_router(advanced_router)


@router.get(
    "",
    response_model=APIResponse[List[SimulatorInfoResponse]],
    summary="Listar simuladores disponibles",
    description="Obtiene la lista de todos los simuladores profesionales disponibles",
)
async def list_simulators(
    _current_user: dict = Depends(get_current_user),
) -> APIResponse[List[SimulatorInfoResponse]]:
    """
    Lista todos los simuladores profesionales disponibles en el sistema.

    **Simuladores implementados:**
    - PO-IA: Product Owner
    - SM-IA: Scrum Master
    - IT-IA: Technical Interviewer
    - IR-IA: Incident Responder
    - CX-IA: Client
    - DSO-IA: DevSecOps
    """
    simulators = [
        SimulatorInfoResponse(
            type=SimulatorType.PRODUCT_OWNER,
            name="Product Owner (PO-IA)",
            description="Simula un Product Owner que revisa requisitos, prioriza backlog y cuestiona decisiones técnicas",
            competencies=["comunicacion_tecnica", "analisis_requisitos", "priorizacion"],
            status="active",
        ),
        SimulatorInfoResponse(
            type=SimulatorType.SCRUM_MASTER,
            name="Scrum Master (SM-IA)",
            description="Simula un Scrum Master que facilita daily standups y gestiona impedimentos",
            competencies=["gestion_tiempo", "comunicacion", "identificacion_impedimentos"],
            status="active",
        ),
        SimulatorInfoResponse(
            type=SimulatorType.TECH_INTERVIEWER,
            name="Technical Interviewer (IT-IA)",
            description="Simula un entrevistador técnico que evalúa conocimientos conceptuales y algorítmicos",
            competencies=["dominio_conceptual", "analisis_algoritmico", "comunicacion_tecnica"],
            status="active",
        ),
        SimulatorInfoResponse(
            type=SimulatorType.INCIDENT_RESPONDER,
            name="Incident Responder (IR-IA)",
            description="Simula un ingeniero DevOps que gestiona incidentes en producción",
            competencies=["diagnostico_sistematico", "priorizacion", "documentacion"],
            status="development",
        ),
        SimulatorInfoResponse(
            type=SimulatorType.CLIENT,
            name="Client (CX-IA)",
            description="Simula un cliente con requisitos ambiguos que requiere elicitación y negociación",
            competencies=["elicitacion_requisitos", "negociacion", "empatia"],
            status="development",
        ),
        SimulatorInfoResponse(
            type=SimulatorType.DEVSECOPS,
            name="DevSecOps (DSO-IA)",
            description="Simula un analista de seguridad que audita código y detecta vulnerabilidades",
            competencies=["seguridad", "analisis_vulnerabilidades", "gestion_riesgo"],
            status="active",
        ),
    ]

    return APIResponse(
        success=True,
        data=simulators,
        message=f"Se encontraron {len(simulators)} simuladores",
    )


@router.post(
    "/interact",
    response_model=APIResponse[SimulatorInteractionResponse],
    summary="Interactuar con simulador",
    description="Procesa una interacción con un simulador profesional (HU-EST-009). SPRINT 4: Usa LLM real (Gemini/OpenAI) para respuestas dinámicas",
)
async def interact_with_simulator(
    request: SimulatorInteractionRequest,
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
    trace_repo: TraceRepository = Depends(get_trace_repository),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    x_flow_id: Optional[str] = Header(None, alias="X-Flow-Id"),
) -> APIResponse[SimulatorInteractionResponse]:
    """
    Procesa una interacción entre el estudiante y un simulador profesional.

    **SPRINT 4**: Ahora usa LLM real (Gemini/OpenAI configurado en .env) para
    generar respuestas dinámicas y contextuales en lugar de respuestas predefinidas.

    **Flujo:**
    1. Valida que la sesión exista y esté activa
    2. Crea el simulador del tipo solicitado **con LLM provider inyectado**
    3. Procesa la entrada del estudiante (usa LLM si disponible, fallback a predefinidas)
    4. Analiza competencias transversales cuantitativamente
    5. Captura traza N4 de la interacción con métricas de competencias
    6. Retorna la respuesta del simulador con scores de competencias

    **HU-EST-009**: Permite al estudiante interactuar con Product Owner simulado
    para desarrollar habilidades de comunicación técnica.
    """
    flow_id = x_flow_id or f"flow_{uuid4()}"
    started_at = time.perf_counter()
    try:
        # ============================================================
        # VALIDACIÓN DE ENTRADA
        # FIX Cortez52: Use custom exceptions
        # ============================================================
        if not request or not request.session_id:
            logger.error("Missing or invalid request data")
            raise ValidationError("Request data is required with a valid session_id", field="session_id")

        if not request.prompt or request.prompt.strip() == "":
            logger.warning("Empty prompt for session %s", request.session_id)
            raise EmptyPromptError()

        logger.info(
            "HTTP simulator interaction received",
            extra={
                "flow_id": flow_id,
                "session_id": request.session_id,
                "simulator_type": str(request.simulator_type),
            },
        )

        # ============================================================
        # VALIDAR SESIÓN
        # FIX Cortez52: Use custom exceptions
        # ============================================================
        try:
            db_session = session_repo.get_by_id(request.session_id)
        except Exception as e:
            logger.error(
                "Error fetching session %s: %s: %s",
                request.session_id,
                type(e).__name__,
                e,
                extra={"flow_id": flow_id, "session_id": request.session_id},
                exc_info=True,
            )
            raise DatabaseOperationError("get_session", details=str(e))

        if not db_session:
            logger.warning("Session not found: %s", request.session_id)
            raise SessionNotFoundError(request.session_id)

        if db_session.status != "active":
            logger.warning(
                "Session %s is not active: %s", request.session_id, db_session.status
            )
            raise SessionInactiveError(request.session_id, db_session.status)

        # ============================================================
        # MAPEAR TIPO DE SIMULADOR
        # ============================================================
        simulator_type_map = {
            SimulatorType.PRODUCT_OWNER: AgentSimulatorType.PRODUCT_OWNER,
            SimulatorType.SCRUM_MASTER: AgentSimulatorType.SCRUM_MASTER,
            SimulatorType.TECH_INTERVIEWER: AgentSimulatorType.TECH_INTERVIEWER,
            SimulatorType.INCIDENT_RESPONDER: AgentSimulatorType.INCIDENT_RESPONDER,
            SimulatorType.CLIENT: AgentSimulatorType.CLIENT,
            SimulatorType.DEVSECOPS: AgentSimulatorType.DEVSECOPS,
        }

        if request.simulator_type not in simulator_type_map:
            logger.error("Unknown simulator type: %s", request.simulator_type)
            raise SimulatorNotSupportedError(str(request.simulator_type))

        agent_simulator_type = simulator_type_map[request.simulator_type]

        # ============================================================
        # CREAR SIMULADOR CON MANEJO DE ERRORES
        # FIX Cortez52: Use custom exceptions
        # ============================================================
        try:
            simulator = SimuladorProfesionalAgent(
                simulator_type=agent_simulator_type,
                llm_provider=llm_provider,
                trace_repo=trace_repo,
                config={"context": request.context or {}, "flow_id": flow_id},
            )
        except Exception as e:
            logger.error(
                "Error creating simulator: %s: %s", type(e).__name__, e, exc_info=True
            )
            raise SimulatorCreationError(str(e))

        # ============================================================
        # PROCESAR INTERACCIÓN CON MANEJO DE ERRORES
        # FIX Cortez52: Use custom exceptions
        # ============================================================
        try:
            response = await simulator.interact(
                student_input=request.prompt,
                context=request.context,
                session_id=request.session_id,
            )
        except ValueError as ve:
            logger.error(
                "Validation error in simulator interaction: %s", ve, exc_info=True
            )
            raise ValidationError(f"Error de validación: {str(ve)}")
        except Exception as e:
            logger.error(
                "Error in simulator interaction: %s: %s",
                type(e).__name__,
                e,
                exc_info=True,
            )
            raise SimulatorInteractionError(str(e))

        # ============================================================
        # CAPTURAR TRAZAS N4
        # ============================================================
        try:
            input_trace = CognitiveTrace(
                session_id=request.session_id,
                student_id=db_session.student_id,
                activity_id=db_session.activity_id,
                trace_level=TraceLevel.N4_COGNITIVO,
                interaction_type=InteractionType.STUDENT_PROMPT,
                content=request.prompt,
                cognitive_state="exploracion",
                cognitive_intent=f"Interactuar con simulador {request.simulator_type.value}",
                ai_involvement=0.0,
                metadata={
                    "simulator_type": request.simulator_type.value,
                    "context": request.context or {},
                },
            )

            output_trace = CognitiveTrace(
                session_id=request.session_id,
                student_id=db_session.student_id,
                activity_id=db_session.activity_id,
                trace_level=TraceLevel.N4_COGNITIVO,
                interaction_type=InteractionType.AI_RESPONSE,
                content=response.get("message", ""),
                cognitive_state="reflexion",
                cognitive_intent=f"Respuesta de simulador {request.simulator_type.value}",
                ai_involvement=1.0,
                metadata={
                    "simulator_type": request.simulator_type.value,
                    "role": response.get("role"),
                    "expects": response.get("expects", []),
                    "competencies_evaluated": response.get("metadata", {}).get(
                        "competencies_evaluated", []
                    ),
                },
            )

            # Persistir trazas
            db_input_trace = trace_repo.create(input_trace)
            db_output_trace = trace_repo.create(output_trace)

        except Exception as e:
            logger.error(
                "Error creating traces (non-critical): %s: %s",
                type(e).__name__,
                e,
                exc_info=True,
            )
            # Continuar sin trazas si falla (no es crítico)
            db_input_trace = type("obj", (object,), {"id": "trace_error_input"})()
            db_output_trace = type("obj", (object,), {"id": "trace_error_output"})()

        # ============================================================
        # PREPARAR RESPUESTA
        # ============================================================
        try:
            simulator_response = SimulatorInteractionResponse(
                interaction_id=f"{db_input_trace.id}_{db_output_trace.id}",
                simulator_type=request.simulator_type,
                response=response.get("message", "Error: No response generated"),
                role=response.get("role", request.simulator_type.value),
                expects=response.get("expects", []),
                competencies_evaluated=response.get("metadata", {}).get(
                    "competencies_evaluated", []
                ),
                trace_id_input=db_input_trace.id,
                trace_id_output=db_output_trace.id,
                metadata={
                    "session_id": request.session_id,
                    "simulator_context": request.context or {},
                    "error": response.get("metadata", {}).get("error")
                    if "error" in response.get("metadata", {})
                    else None,
                },
            )

            logger.info(
                "HTTP simulator interaction completed",
                extra={
                    "flow_id": flow_id,
                    "session_id": request.session_id,
                    "simulator_type": str(request.simulator_type),
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                },
            )
            return APIResponse(
                success=True,
                data=simulator_response,
                message=f"Interacción procesada con simulador {request.simulator_type.value}",
            )

        except Exception as e:
            logger.error(
                "Error building simulator response: %s: %s",
                type(e).__name__,
                e,
                exc_info=True,
            )
            raise SimulatorInteractionError(f"Error al construir la respuesta: {str(e)}")

    except (ValidationError, EmptyPromptError, SessionNotFoundError, SessionInactiveError,
            SimulatorNotSupportedError, SimulatorCreationError, SimulatorInteractionError,
            DatabaseOperationError):
        # FIX Cortez52: Re-raise custom exceptions without wrapping
        raise
    except Exception as e:
        logger.error(
            "Unexpected critical error in interact_with_simulator: %s: %s",
            type(e).__name__,
            e,
            exc_info=True,
        )
        raise SimulatorInteractionError(f"Error crítico inesperado: {str(e)}")


@router.get(
    "/{simulator_type}",
    response_model=APIResponse[SimulatorInfoResponse],
    summary="Obtener información de simulador",
    description="Obtiene información detallada de un simulador específico",
)
async def get_simulator_info(
    simulator_type: SimulatorType,
) -> APIResponse[SimulatorInfoResponse]:
    """
    Obtiene información detallada de un simulador profesional específico.
    """
    simulators_map = {
        SimulatorType.PRODUCT_OWNER: SimulatorInfoResponse(
            type=SimulatorType.PRODUCT_OWNER,
            name="Product Owner (PO-IA)",
            description="Simula un Product Owner que revisa requisitos, prioriza backlog y cuestiona decisiones técnicas. Evalúa la capacidad del estudiante para comunicar ideas técnicas en lenguaje de negocio y justificar decisiones arquitectónicas.",
            competencies=[
                "comunicacion_tecnica",
                "analisis_requisitos",
                "priorizacion",
                "justificacion_decisiones",
            ],
            status="active",
            example_questions=[
                "¿Cuáles son los criterios de aceptación?",
                "¿Cómo agrega valor al usuario final?",
                "¿Qué alternativas consideraste?",
                "¿Cuál es el impacto si lo postergamos?",
            ],
        ),
        SimulatorType.SCRUM_MASTER: SimulatorInfoResponse(
            type=SimulatorType.SCRUM_MASTER,
            name="Scrum Master (SM-IA)",
            description="Simula un Scrum Master que facilita daily standups, gestiona impedimentos y ayuda al equipo a mejorar procesos ágiles.",
            competencies=[
                "gestion_tiempo",
                "comunicacion",
                "identificacion_impedimentos",
                "auto_organizacion",
            ],
            status="active",
            example_questions=[
                "¿Qué lograste ayer?",
                "¿Qué vas a hacer hoy?",
                "¿Hay algún impedimento?",
                "¿Por qué llevás más tiempo del estimado?",
            ],
        ),
        SimulatorType.TECH_INTERVIEWER: SimulatorInfoResponse(
            type=SimulatorType.TECH_INTERVIEWER,
            name="Technical Interviewer (IT-IA)",
            description="Simula un entrevistador técnico que evalúa conocimientos conceptuales, algorítmicos y de diseño de sistemas.",
            competencies=[
                "dominio_conceptual",
                "analisis_algoritmico",
                "comunicacion_tecnica",
                "razonamiento_en_voz_alta",
            ],
            status="active",
            example_questions=[
                "Explicá la diferencia entre O(n) y O(log n)",
                "¿Cómo invertirías una lista enlazada?",
                "¿Cómo diseñarías un sistema de caché?",
            ],
        ),
        SimulatorType.INCIDENT_RESPONDER: SimulatorInfoResponse(
            type=SimulatorType.INCIDENT_RESPONDER,
            name="Incident Responder (IR-IA)",
            description="Simula un ingeniero DevOps que gestiona incidentes en producción bajo presión.",
            competencies=[
                "diagnostico_sistematico",
                "priorizacion",
                "documentacion",
                "manejo_presion",
            ],
            status="development",
        ),
        SimulatorType.CLIENT: SimulatorInfoResponse(
            type=SimulatorType.CLIENT,
            name="Client (CX-IA)",
            description="Simula un cliente con requisitos ambiguos que requiere elicitación, negociación y gestión de expectativas.",
            competencies=[
                "elicitacion_requisitos",
                "negociacion",
                "empatia",
                "gestion_expectativas",
            ],
            status="development",
        ),
        SimulatorType.DEVSECOPS: SimulatorInfoResponse(
            type=SimulatorType.DEVSECOPS,
            name="DevSecOps (DSO-IA)",
            description="Simula un analista de seguridad que audita código, detecta vulnerabilidades y exige planes de remediación.",
            competencies=[
                "seguridad",
                "analisis_vulnerabilidades",
                "gestion_riesgo",
                "cumplimiento",
            ],
            status="active",
            example_questions=[
                "¿Cómo vas a remediar esta SQL injection?",
                "¿Por qué hardcodeaste credenciales?",
                "¿Cuál es tu plan de actualización de dependencias?",
            ],
        ),
    }

    simulator_info = simulators_map.get(simulator_type)
    if not simulator_info:
        # FIX Cortez52: Use custom exception
        raise SimulatorNotSupportedError(str(simulator_type))

    return APIResponse(
        success=True,
        data=simulator_info,
        message=f"Información de simulador {simulator_type.value}",
    )
