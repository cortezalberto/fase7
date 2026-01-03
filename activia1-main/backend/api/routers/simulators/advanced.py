"""
Advanced Simulator Endpoints - SM-IA, CX-IA, DSO-IA.

Cortez46: Extracted from monolithic simulators.py (1,589 lines)
Cortez66: Renamed from sprint6.py to advanced.py
FIX Cortez52: Migrated HTTPExceptions to custom exceptions

Contains:
- POST /scrum/daily-standup: Daily standup with Scrum Master (SM-IA)
- POST /client/requirements: Get client requirements (CX-IA)
- POST /client/clarify: Ask client clarification (CX-IA)
- POST /security/audit: Security code audit (DSO-IA)

Sprint 6 - HU-EST-010, HU-EST-013, HU-EST-014
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ...deps import get_db, get_llm_provider, get_current_user
from ...schemas.common import APIResponse
from ...schemas.simulators import (
    DailyStandupRequest,
    DailyStandupResponse,
    ClientRequirementRequest,
    ClientClarificationRequest,
    ClientResponse,
    SecurityAuditRequest,
    SecurityAuditResponse,
    SecurityVulnerability,
)
from ...exceptions import (
    SessionNotFoundError,
    DatabaseOperationError,
)
from ....agents.simulators import SimuladorProfesionalAgent
from ....database.repositories import SessionRepository, TraceRepository
from ....models.trace import TraceLevel, InteractionType
from ....llm.base import LLMProvider

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sprint 6 Advanced Simulators"])


# ============================================================================
# SCRUM MASTER SIMULATOR (SM-IA) - HU-EST-010
# ============================================================================


@router.post(
    "/scrum/daily-standup",
    response_model=APIResponse[DailyStandupResponse],
    summary="Daily Standup with Scrum Master (SM-IA)",
    description="Participar en daily standup simulado con feedback del Scrum Master",
)
async def daily_standup(
    request: DailyStandupRequest,
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[DailyStandupResponse]:
    """
    Procesa la participación del estudiante en un daily standup simulado.

    El Scrum Master (SM-IA) analiza:
    - Claridad y concisión de la comunicación
    - Identificación de impedimentos
    - Comprensión de compromisos del sprint
    - Detección de problemas (scope creep, bloqueos, falta de foco)

    Args:
        request: Daily standup data
        db: Database session
        llm_provider: LLM provider

    Returns:
        APIResponse con feedback del SM-IA
    """
    logger.info(
        "Processing daily standup for student %s",
        request.student_id,
        extra={
            "student_id": request.student_id,
            "session_id": request.session_id,
            "activity_id": request.activity_id,
        },
    )

    try:
        # Verificar que la sesión existe
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Crear agente SM-IA
        sm_agent = SimuladorProfesionalAgent(
            simulator_type=None,  # SM-IA no requiere tipo específico
            llm_provider=llm_provider,
        )

        # Procesar daily standup
        feedback_data = sm_agent.procesar_daily_standup(
            ayer=request.what_did_yesterday,
            hoy=request.what_will_do_today,
            impedimentos=request.impediments,
        )

        # Crear trace de la interacción
        trace_repo = TraceRepository(db)
        trace_repo.create(
            student_id=request.student_id,
            activity_id=request.activity_id or "daily_standup",
            trace_level=TraceLevel.N3_INTERACCIONAL,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=f"Daily standup: {request.what_did_yesterday[:50]}...",
            ai_involvement=0.5,  # Moderada participación del AI
        )

        logger.info(
            "Daily standup processed successfully",
            extra={
                "student_id": request.student_id,
                "issues_detected": len(feedback_data.get("detected_issues", [])),
            },
        )

        # Construir response
        response = DailyStandupResponse(
            feedback=feedback_data.get("feedback", ""),
            questions=feedback_data.get("questions", []),
            detected_issues=feedback_data.get("detected_issues", []),
            suggestions=feedback_data.get("suggestions", []),
        )

        return APIResponse(
            success=True,
            data=response,
            message="Daily standup feedback generated successfully",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error("Error processing daily standup", exc_info=True)
        raise DatabaseOperationError("process_daily_standup", details=str(e))


# ============================================================================
# CLIENT SIMULATOR (CX-IA) - HU-EST-013
# ============================================================================


@router.post(
    "/client/requirements",
    response_model=APIResponse[ClientResponse],
    summary="Get Client Requirements (CX-IA)",
    description="Obtener requisitos iniciales del cliente simulado",
)
async def get_client_requirements(
    request: ClientRequirementRequest,
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[ClientResponse]:
    """
    Obtiene los requisitos iniciales del cliente simulado (CX-IA).

    El cliente presenta requisitos ambiguos, contradictorios o incompletos
    para entrenar habilidades de elicitación y comunicación.

    Args:
        request: Client requirement request
        db: Database session
        llm_provider: LLM provider

    Returns:
        APIResponse con requisitos del cliente
    """
    logger.info(
        "Generating client requirements for student %s",
        request.student_id,
        extra={
            "student_id": request.student_id,
            "project_type": request.project_type,
        },
    )

    try:
        # Verificar sesión
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Crear agente CX-IA
        cx_agent = SimuladorProfesionalAgent(
            simulator_type=None,
            llm_provider=llm_provider,
        )

        # Generar requisitos del cliente
        client_data = cx_agent.generar_requerimientos_cliente(
            tipo_proyecto=request.project_type
        )

        # Crear trace
        trace_repo = TraceRepository(db)
        trace_repo.create(
            student_id=request.student_id,
            activity_id=request.activity_id or "client_requirements",
            trace_level=TraceLevel.N3_INTERACCIONAL,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=f"Client requirements request: {request.project_type}",
            ai_involvement=0.7,  # Alta participación del AI en generación
        )

        logger.info("Client requirements generated successfully")

        # Construir response
        response = ClientResponse(
            response=client_data.get("requirements", ""),
            additional_requirements=client_data.get("additional_requirements"),
            evaluation={
                "empathy": 0.0,
                "clarity": 0.0,
                "professionalism": 0.0,
            },  # Aún no hay evaluación
        )

        return APIResponse(
            success=True,
            data=response,
            message="Client requirements generated successfully",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error("Error generating client requirements", exc_info=True)
        raise DatabaseOperationError("generate_client_requirements", details=str(e))


@router.post(
    "/client/clarify",
    response_model=APIResponse[ClientResponse],
    summary="Ask Client Clarification (CX-IA)",
    description="Hacer pregunta de clarificación al cliente",
)
async def ask_client_clarification(
    request: ClientClarificationRequest,
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[ClientResponse]:
    """
    Envía una pregunta de clarificación al cliente simulado (CX-IA).

    El cliente evalúa las soft skills del estudiante:
    - Empatía (tono, consideración)
    - Claridad (precisión de la pregunta)
    - Profesionalismo (formalidad, respeto)

    Args:
        request: Clarification question
        db: Database session
        llm_provider: LLM provider

    Returns:
        APIResponse con respuesta del cliente y evaluación de soft skills
    """
    logger.info(
        "Processing client clarification question",
        extra={"session_id": request.session_id},
    )

    try:
        # Verificar sesión
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Crear agente CX-IA
        cx_agent = SimuladorProfesionalAgent(
            simulator_type=None,
            llm_provider=llm_provider,
        )

        # Responder clarificación
        client_data = cx_agent.responder_clarificacion(pregunta=request.question)

        # Crear trace
        trace_repo = TraceRepository(db)
        trace_repo.create(
            student_id=session_db.student_id,
            activity_id=session_db.activity_id,
            trace_level=TraceLevel.N3_INTERACCIONAL,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=f"Client clarification: {request.question[:100]}...",
            ai_involvement=0.6,
        )

        logger.info("Client clarification processed successfully")

        # Construir response
        response = ClientResponse(
            response=client_data.get("response", ""),
            additional_requirements=client_data.get("additional_requirements"),
            evaluation=client_data.get(
                "soft_skills",
                {
                    "empathy": 0.5,
                    "clarity": 0.5,
                    "professionalism": 0.5,
                },
            ),
        )

        return APIResponse(
            success=True,
            data=response,
            message="Client clarification answered successfully",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error("Error processing client clarification", exc_info=True)
        raise DatabaseOperationError("process_client_clarification", details=str(e))


# ============================================================================
# DEVSECOPS AUDITOR (DSO-IA) - HU-EST-014
# ============================================================================


@router.post(
    "/security/audit",
    response_model=APIResponse[SecurityAuditResponse],
    summary="Security Code Audit (DSO-IA)",
    description="Auditar código en busca de vulnerabilidades de seguridad (OWASP Top 10)",
)
async def security_audit(
    request: SecurityAuditRequest,
    db: Session = Depends(get_db),
    llm_provider: LLMProvider = Depends(get_llm_provider),
    current_user: dict = Depends(get_current_user),  # FIX Cortez69 CRIT-API-001
) -> APIResponse[SecurityAuditResponse]:
    """
    Realiza una auditoría de seguridad del código proporcionado (DSO-IA).

    Detecta vulnerabilidades de OWASP Top 10:
    - SQL Injection
    - XSS (Cross-Site Scripting)
    - CSRF (Cross-Site Request Forgery)
    - Secrets hardcodeados
    - Code injection (eval, exec)
    - Path traversal
    - Weak crypto
    - Etc.

    Args:
        request: Security audit request with code
        db: Database session
        llm_provider: LLM provider

    Returns:
        APIResponse con reporte completo de seguridad
    """
    logger.info(
        "Starting security audit for student %s",
        request.student_id,
        extra={
            "student_id": request.student_id,
            "language": request.language,
            "code_length": len(request.code),
        },
    )

    try:
        # Verificar sesión
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Crear agente DSO-IA
        dso_agent = SimuladorProfesionalAgent(
            simulator_type=None,
            llm_provider=llm_provider,
        )

        # Realizar auditoría de seguridad
        audit_data = dso_agent.auditar_seguridad(
            codigo=request.code,
            lenguaje=request.language,
        )

        # Crear trace
        trace_repo = TraceRepository(db)
        trace_repo.create(
            student_id=request.student_id,
            activity_id=request.activity_id or "security_audit",
            trace_level=TraceLevel.N3_INTERACCIONAL,
            interaction_type=InteractionType.STUDENT_PROMPT,
            content=f"Security audit ({request.language}): {len(request.code)} chars",
            ai_involvement=0.8,  # Alta participación del AI en análisis
        )

        # Convertir vulnerabilidades a SecurityVulnerability objects
        vulnerabilities = []
        for vuln in audit_data.get("vulnerabilities", []):
            vulnerabilities.append(
                SecurityVulnerability(
                    severity=vuln.get("severity", "INFO"),
                    vulnerability_type=vuln.get("vulnerability_type", "UNKNOWN"),
                    line_number=vuln.get("line_number"),
                    description=vuln.get("description", ""),
                    recommendation=vuln.get("recommendation", ""),
                    cwe_id=vuln.get("cwe_id"),
                    owasp_category=vuln.get("owasp_category"),
                )
            )

        logger.info(
            "Security audit completed",
            extra={
                "total_vulnerabilities": audit_data.get("total_vulnerabilities", 0),
                "critical_count": audit_data.get("critical_count", 0),
                "security_score": audit_data.get("security_score", 10.0),
            },
        )

        # Construir response
        response = SecurityAuditResponse(
            audit_id=f"audit_{session_db.id[:8]}",
            total_vulnerabilities=audit_data.get("total_vulnerabilities", 0),
            critical_count=audit_data.get("critical_count", 0),
            high_count=audit_data.get("high_count", 0),
            medium_count=audit_data.get("medium_count", 0),
            low_count=audit_data.get("low_count", 0),
            vulnerabilities=vulnerabilities,
            overall_security_score=audit_data.get("security_score", 10.0),
            recommendations=audit_data.get("recommendations", []),
            compliant_with_owasp=audit_data.get("owasp_compliant", True),
        )

        return APIResponse(
            success=True,
            data=response,
            message=f"Security audit completed: {len(vulnerabilities)} vulnerabilities found",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error("Error performing security audit", exc_info=True)
        raise DatabaseOperationError("perform_security_audit", details=str(e))
