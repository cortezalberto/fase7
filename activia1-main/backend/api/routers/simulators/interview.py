"""
Interview Simulator Endpoints (IT-IA) - Technical Interview Simulation.

Cortez46: Extracted from monolithic simulators.py (1,589 lines)
FIX Cortez52: Migrated HTTPExceptions to custom exceptions

Contains:
- POST /interview/start: Start technical interview
- POST /interview/respond: Submit interview response
- POST /interview/complete: Complete interview with evaluation
- GET /interview/{interview_id}: Get interview details

Sprint 6 - HU-EST-011
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ...deps import get_db
from ...schemas.common import APIResponse
from ...schemas.simulators import (
    InterviewStartRequest,
    InterviewResponseRequest,
    InterviewCompleteRequest,
    InterviewResponse,
)
from ...exceptions import (
    SessionNotFoundError,
    InterviewNotFoundError,
    DatabaseOperationError,
)
from ....agents.simulators import SimuladorProfesionalAgent, SimuladorType
from ....database.repositories import SessionRepository, InterviewSessionRepository
from ....llm.factory import LLMProviderFactory

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Interview Simulator (IT-IA)"])


@router.post(
    "/interview/start",
    response_model=APIResponse[InterviewResponse],
    summary="Start Technical Interview (Sprint 6)",
    description="Inicia una simulación de entrevista técnica con IT-IA (Technical Interviewer Agent)",
)
async def start_interview(
    request: InterviewStartRequest,
    db: Session = Depends(get_db),
) -> APIResponse[InterviewResponse]:
    """
    Inicia una sesión de entrevista técnica simulada (SPRINT 6).

    El agente IT-IA generará preguntas basadas en:
    - Tipo de entrevista (CONCEPTUAL, ALGORITHMIC, DESIGN, BEHAVIORAL)
    - Nivel de dificultad (EASY, MEDIUM, HARD)
    - Contexto de la sesión AI-Native

    Returns:
        InterviewResponse con la primera pregunta generada
    """
    try:
        # Validate session exists
        session_repo = SessionRepository(db)
        session_db = session_repo.get_by_id(request.session_id)
        if not session_db:
            raise SessionNotFoundError(request.session_id)

        # Create interview session
        interview_repo = InterviewSessionRepository(db)
        interview = interview_repo.create(
            session_id=request.session_id,
            student_id=request.student_id,
            interview_type=request.interview_type,
            activity_id=request.activity_id,
            difficulty_level=request.difficulty_level,
        )

        # Initialize simulator and generate first question
        # FIX Cortez54: Added required simulator_type argument
        llm_provider = LLMProviderFactory.create_from_env()
        simulator = SimuladorProfesionalAgent(
            simulator_type=SimuladorType.TECH_INTERVIEWER,
            llm_provider=llm_provider
        )

        first_question = await simulator.generar_pregunta_entrevista(
            tipo_entrevista=request.interview_type,
            dificultad=request.difficulty_level,
            contexto=f"Estudiante: {request.student_id}, Actividad: {request.activity_id}",
        )

        # Add first question to interview
        question_data = {
            "question": first_question,
            "type": request.interview_type,
            "timestamp": interview.created_at.isoformat(),
        }
        interview = interview_repo.add_question(interview.id, question_data)

        logger.info(
            "Interview started",
            extra={
                "interview_id": interview.id,
                "student_id": request.student_id,
                "interview_type": request.interview_type,
            },
        )

        return APIResponse(
            success=True,
            data=InterviewResponse(
                interview_id=interview.id,
                session_id=interview.session_id,
                student_id=interview.student_id,
                interview_type=interview.interview_type,
                difficulty_level=interview.difficulty_level,
                questions_asked=interview.questions_asked,
                responses=interview.responses,
                created_at=interview.created_at,
                updated_at=interview.updated_at,
            ),
            message="Technical interview started successfully",
        )

    except SessionNotFoundError:
        raise
    except Exception as e:
        logger.error(
            "Error starting interview",
            exc_info=True,
            extra={"student_id": request.student_id},
        )
        raise DatabaseOperationError("start_interview", details=str(e))


@router.post(
    "/interview/respond",
    response_model=APIResponse[InterviewResponse],
    summary="Submit Interview Response (Sprint 6)",
    description="Envía la respuesta del estudiante a una pregunta de entrevista",
)
async def submit_interview_response(
    request: InterviewResponseRequest,
    db: Session = Depends(get_db),
) -> APIResponse[InterviewResponse]:
    """
    Procesa la respuesta del estudiante y genera la siguiente pregunta (SPRINT 6).

    El agente IT-IA evaluará:
    - Claridad de comunicación
    - Precisión técnica
    - Proceso de pensamiento (thinking aloud)
    - Puntos clave cubiertos
    """
    try:
        interview_repo = InterviewSessionRepository(db)
        interview = interview_repo.get_by_id(request.interview_id)

        if not interview:
            raise InterviewNotFoundError(request.interview_id)

        # Evaluate response with IT-IA
        # FIX Cortez54: Added required simulator_type argument
        llm_provider = LLMProviderFactory.create_from_env()
        simulator = SimuladorProfesionalAgent(
            simulator_type=SimuladorType.TECH_INTERVIEWER,
            llm_provider=llm_provider
        )

        last_question = interview.questions_asked[-1] if interview.questions_asked else {}

        evaluation = await simulator.evaluar_respuesta_entrevista(
            pregunta=last_question.get("question", ""),
            respuesta=request.response,
            tipo_entrevista=interview.interview_type,
        )

        # Add response with evaluation
        response_data = {
            "response": request.response,
            "timestamp": interview.updated_at.isoformat(),
            "evaluation": evaluation,
        }
        interview = interview_repo.add_response(interview.id, response_data)

        # Generate next question if interview not complete
        if len(interview.questions_asked) < 5:  # Max 5 questions per interview
            next_question = await simulator.generar_pregunta_entrevista(
                tipo_entrevista=interview.interview_type,
                dificultad=interview.difficulty_level,
                contexto=f"Preguntas previas: {len(interview.questions_asked)}",
            )

            question_data = {
                "question": next_question,
                "type": interview.interview_type,
                "timestamp": interview.updated_at.isoformat(),
            }
            interview = interview_repo.add_question(interview.id, question_data)

        logger.info(
            "Interview response processed",
            extra={
                "interview_id": interview.id,
                "question_count": len(interview.questions_asked),
            },
        )

        return APIResponse(
            success=True,
            data=InterviewResponse(
                interview_id=interview.id,
                session_id=interview.session_id,
                student_id=interview.student_id,
                interview_type=interview.interview_type,
                difficulty_level=interview.difficulty_level,
                questions_asked=interview.questions_asked,
                responses=interview.responses,
                created_at=interview.created_at,
                updated_at=interview.updated_at,
            ),
            message="Response evaluated successfully",
        )

    except InterviewNotFoundError:
        raise
    except Exception as e:
        logger.error("Error processing interview response", exc_info=True)
        raise DatabaseOperationError("process_interview_response", details=str(e))


@router.post(
    "/interview/complete",
    response_model=APIResponse[InterviewResponse],
    summary="Complete Interview (Sprint 6)",
    description="Finaliza la entrevista y genera evaluación final",
)
async def complete_interview(
    request: InterviewCompleteRequest,
    db: Session = Depends(get_db),
) -> APIResponse[InterviewResponse]:
    """
    Completa la entrevista técnica y genera evaluación final (SPRINT 6).

    Calcula:
    - Score global (0.0 - 1.0)
    - Breakdown por dimensión (clarity, technical_accuracy, communication)
    - Feedback narrativo del evaluador
    """
    try:
        interview_repo = InterviewSessionRepository(db)
        interview = interview_repo.get_by_id(request.interview_id)

        if not interview:
            raise InterviewNotFoundError(request.interview_id)

        # Generate final evaluation
        # FIX Cortez54: Added required simulator_type argument
        llm_provider = LLMProviderFactory.create_from_env()
        simulator = SimuladorProfesionalAgent(
            simulator_type=SimuladorType.TECH_INTERVIEWER,
            llm_provider=llm_provider
        )

        final_evaluation = await simulator.generar_evaluacion_entrevista(
            preguntas=interview.questions_asked,
            respuestas=interview.responses,
            tipo_entrevista=interview.interview_type,
        )

        # Calculate duration
        duration = int(
            (interview.updated_at - interview.created_at).total_seconds() / 60
        )

        # Complete interview with evaluation
        interview = interview_repo.complete_interview(
            interview_id=interview.id,
            evaluation_score=final_evaluation.get("overall_score", 0.0),
            evaluation_breakdown=final_evaluation.get("breakdown", {}),
            feedback=final_evaluation.get("feedback", ""),
            duration_minutes=duration,
        )

        logger.info(
            "Interview completed",
            extra={
                "interview_id": interview.id,
                "score": interview.evaluation_score,
                "duration_minutes": duration,
            },
        )

        return APIResponse(
            success=True,
            data=InterviewResponse(
                interview_id=interview.id,
                session_id=interview.session_id,
                student_id=interview.student_id,
                interview_type=interview.interview_type,
                difficulty_level=interview.difficulty_level,
                questions_asked=interview.questions_asked,
                responses=interview.responses,
                evaluation_score=interview.evaluation_score,
                evaluation_breakdown=interview.evaluation_breakdown,
                feedback=interview.feedback,
                duration_minutes=interview.duration_minutes,
                created_at=interview.created_at,
                updated_at=interview.updated_at,
            ),
            message="Interview completed successfully",
        )

    except InterviewNotFoundError:
        raise
    except Exception as e:
        logger.error("Error completing interview", exc_info=True)
        raise DatabaseOperationError("complete_interview", details=str(e))


@router.get(
    "/interview/{interview_id}",
    response_model=APIResponse[InterviewResponse],
    summary="Get Interview Details (Sprint 6)",
    description="Obtiene detalles completos de una sesión de entrevista",
)
async def get_interview(
    interview_id: str,
    db: Session = Depends(get_db),
) -> APIResponse[InterviewResponse]:
    """Obtiene detalles completos de una entrevista técnica (SPRINT 6)"""
    try:
        interview_repo = InterviewSessionRepository(db)
        interview = interview_repo.get_by_id(interview_id)

        if not interview:
            raise InterviewNotFoundError(interview_id)

        return APIResponse(
            success=True,
            data=InterviewResponse(
                interview_id=interview.id,
                session_id=interview.session_id,
                student_id=interview.student_id,
                interview_type=interview.interview_type,
                difficulty_level=interview.difficulty_level,
                questions_asked=interview.questions_asked,
                responses=interview.responses,
                evaluation_score=interview.evaluation_score,
                evaluation_breakdown=interview.evaluation_breakdown,
                feedback=interview.feedback,
                duration_minutes=interview.duration_minutes,
                created_at=interview.created_at,
                updated_at=interview.updated_at,
            ),
        )

    except InterviewNotFoundError:
        raise
    except Exception as e:
        logger.error("Error retrieving interview", exc_info=True)
        raise DatabaseOperationError("retrieve_interview", details=str(e))
