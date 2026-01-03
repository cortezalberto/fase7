"""
Training Endpoints - API route handlers for Digital Training.

Cortez46: Extracted from training.py (1,620 lines)
Cortez51: Migrated HTTPExceptions to custom exceptions
FIX Cortez52: Fixed N+1 queries using batch loading methods

Contains endpoints for:
- /lenguajes: Get available programming languages and lessons
- /materias: Legacy endpoint for subjects
- /iniciar: Start training session
- /submit-ejercicio: Submit exercise code
- /pista: Request hint
- /corregir-ia: AI-based code correction
- /sesion/{id}/estado: Get session state
- /sesion/{id}: Cancel session
- /exercises/{id}/details: Admin endpoint for exercise details
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from backend.database.config import get_db
from backend.api.deps import get_current_user, get_llm_provider, require_teacher_role
from backend.database.models import UserDB as User, ExerciseAttemptDB
from backend.llm.base import LLMMessage, LLMRole
from backend.services.code_evaluator import CodeEvaluator
from backend.database.repositories import (
    SubjectRepository,
    ExerciseRepository,
    ExerciseHintRepository,
    ExerciseTestRepository,
    ExerciseAttemptRepository
)
from backend.api.exceptions import (
    ExerciseNotFoundError,
    SessionNotFoundError,
    AuthorizationError,
    ValidationError,
    DatabaseOperationError,
)

from .schemas import (
    LenguajeInfo, LeccionInfo, EjercicioInfo,
    MateriaInfo, TemaInfo,
    IniciarEntrenamientoRequest, SesionEntrenamiento, EjercicioActual,
    SubmitEjercicioRequest, ResultadoEjercicio, ResultadoFinal,
    SolicitarPistaRequest, PistaResponse,
    CorreccionIARequest, CorreccionIAResponse,
    SesionEntrenamientoExtendida, CognitiveStateEnum
)
from .session_storage import guardar_sesion, obtener_sesion, listar_sesiones_activas
from .helpers import NOMBRES_LECCIONES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/training", tags=["Digital Training"])


@router.get("/lenguajes", response_model=List[LenguajeInfo])
async def obtener_lenguajes_disponibles(db: Session = Depends(get_db)):
    """
    Obtiene la lista de lenguajes de programación disponibles con sus lecciones
    Devuelve estructura jerárquica: Lenguaje → Lecciones → Ejercicios

    FIX Cortez54: Now queries exercises directly by language, not just through subjects
    """
    try:
        subject_repo = SubjectRepository(db)
        exercise_repo = ExerciseRepository(db)

        lenguajes_dict: Dict[str, Dict[str, Any]] = {}

        # FIX Cortez54: First try to get all exercises directly (new approach)
        # This works even if subjects table is empty
        all_exercises = exercise_repo.get_all(active_only=True)

        if all_exercises:
            # New approach: Build from exercises directly
            for exercise in all_exercises:
                language = exercise.language
                if not language:
                    continue

                if language not in lenguajes_dict:
                    nombre_completo = "Python 3.11+" if language == "python" else "Java 17" if language == "java" else language.title()
                    lenguajes_dict[language] = {
                        "language": language,
                        "nombre_completo": nombre_completo,
                        "lecciones_dict": {}
                    }

                unit = exercise.unit or 1
                unit_key = f"{language}_UNIT_{unit}"

                if unit_key not in lenguajes_dict[language]["lecciones_dict"]:
                    nombre_leccion = NOMBRES_LECCIONES.get(unit, f"Unidad {unit}")
                    lenguajes_dict[language]["lecciones_dict"][unit_key] = {
                        "id": unit_key,
                        "nombre": nombre_leccion,
                        "descripcion": f"Ejercicios de {nombre_leccion.lower()}",
                        "unit_number": unit,
                        "ejercicios": [],
                        "total_puntos": 0,
                        "dificultades": []
                    }

                ejercicio_info = EjercicioInfo(
                    id=exercise.id,
                    titulo=exercise.title,
                    dificultad=exercise.difficulty,
                    tiempo_estimado_min=exercise.time_min,
                    puntos=exercise.max_score or 100
                )

                lenguajes_dict[language]["lecciones_dict"][unit_key]["ejercicios"].append(ejercicio_info)
                lenguajes_dict[language]["lecciones_dict"][unit_key]["total_puntos"] += exercise.max_score or 100
                lenguajes_dict[language]["lecciones_dict"][unit_key]["dificultades"].append(exercise.difficulty)
        else:
            # Fallback: Legacy approach using subjects
            subjects = subject_repo.get_all(active_only=True)

            for subject in subjects:
                exercises = exercise_repo.get_by_subject(subject.code)
                if not exercises:
                    continue

                language = subject.language
                if not language:
                    continue

                if language not in lenguajes_dict:
                    nombre_completo = "Python 3.11+" if language == "python" else "Java 17" if language == "java" else language.title()
                    lenguajes_dict[language] = {
                        "language": language,
                        "nombre_completo": nombre_completo,
                        "lecciones_dict": {}
                    }

                for exercise in exercises:
                    unit = exercise.unit or 1
                    unit_key = f"{language}_UNIT_{unit}"

                    if unit_key not in lenguajes_dict[language]["lecciones_dict"]:
                        nombre_leccion = NOMBRES_LECCIONES.get(unit, f"Unidad {unit}")
                        lenguajes_dict[language]["lecciones_dict"][unit_key] = {
                            "id": unit_key,
                            "nombre": nombre_leccion,
                            "descripcion": f"Ejercicios de {nombre_leccion.lower()}",
                            "unit_number": unit,
                            "ejercicios": [],
                            "total_puntos": 0,
                            "dificultades": []
                        }

                    ejercicio_info = EjercicioInfo(
                        id=exercise.id,
                        titulo=exercise.title,
                        dificultad=exercise.difficulty,
                        tiempo_estimado_min=exercise.time_min,
                        puntos=exercise.max_score or 100
                    )

                    lenguajes_dict[language]["lecciones_dict"][unit_key]["ejercicios"].append(ejercicio_info)
                    lenguajes_dict[language]["lecciones_dict"][unit_key]["total_puntos"] += exercise.max_score or 100
                    lenguajes_dict[language]["lecciones_dict"][unit_key]["dificultades"].append(exercise.difficulty)

        lenguajes_list = []
        for lang_data in lenguajes_dict.values():
            lecciones_list = []
            for leccion_data in lang_data["lecciones_dict"].values():
                dificultades = leccion_data["dificultades"]
                if "Hard" in dificultades or "Difícil" in dificultades:
                    dificultad_leccion = "Difícil"
                elif "Medium" in dificultades or "Media" in dificultades:
                    dificultad_leccion = "Media"
                else:
                    dificultad_leccion = "Fácil"

                lecciones_list.append(LeccionInfo(
                    id=leccion_data["id"],
                    nombre=leccion_data["nombre"],
                    descripcion=leccion_data["descripcion"],
                    unit_number=leccion_data["unit_number"],
                    ejercicios=leccion_data["ejercicios"],
                    total_puntos=leccion_data["total_puntos"],
                    dificultad=dificultad_leccion
                ))

            lecciones_list.sort(key=lambda x: x.unit_number)
            lenguajes_list.append(LenguajeInfo(
                language=lang_data["language"],
                nombre_completo=lang_data["nombre_completo"],
                lecciones=lecciones_list
            ))

        logger.info("Loaded %d languages with lecciones from database", len(lenguajes_list))
        return lenguajes_list

    except Exception as e:
        logger.error("Error obteniendo lenguajes desde BD: %s", e, exc_info=True)
        raise DatabaseOperationError("load_languages", details=str(e))


@router.get("/materias", response_model=List[MateriaInfo])
async def obtener_materias_disponibles(db: Session = Depends(get_db)):
    """
    LEGACY ENDPOINT - Usar /lenguajes para la nueva estructura jerárquica
    """
    try:
        subject_repo = SubjectRepository(db)
        exercise_repo = ExerciseRepository(db)
        materias = []

        subjects = subject_repo.get_all(active_only=True)

        for subject in subjects:
            exercises = exercise_repo.get_by_subject(subject.code)
            temas_info = []
            for exercise in exercises:
                temas_info.append(TemaInfo(
                    id=exercise.id,
                    nombre=exercise.title,
                    descripcion=exercise.description[:100] + "..." if len(exercise.description or "") > 100 else (exercise.description or ""),
                    dificultad=exercise.difficulty,
                    tiempo_estimado_min=exercise.time_min
                ))

            if temas_info:
                nombre_materia = "Python" if subject.code == "PROG1" else "Java" if subject.code == "PROG2" else subject.name
                codigo_materia = "PYTHON" if subject.code == "PROG1" else "JAVA" if subject.code == "PROG2" else subject.code
                materias.append(MateriaInfo(
                    materia=nombre_materia,
                    codigo=codigo_materia,
                    temas=temas_info
                ))

        logger.info("Loaded %d materias with %d exercises from database", len(materias), sum(len(m.temas) for m in materias))
        return materias

    except Exception as e:
        logger.error("Error obteniendo materias desde BD: %s", e, exc_info=True)
        raise DatabaseOperationError("load_subjects", details=str(e))


@router.post("/iniciar", response_model=SesionEntrenamiento)
async def iniciar_entrenamiento(
    request: IniciarEntrenamientoRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # FIX Cortez69 HIGH-API-002
):
    """
    Inicia una nueva sesión de entrenamiento.
    """
    try:
        exercise_repo = ExerciseRepository(db)
        hint_repo = ExerciseHintRepository(db)
        test_repo = ExerciseTestRepository(db)

        # Obtener ejercicios
        if request.exercise_id:
            exercises = [exercise_repo.get_by_id(request.exercise_id)]
            if not exercises[0]:
                raise ExerciseNotFoundError(request.exercise_id)
        else:
            exercises = exercise_repo.get_by_language_and_unit(
                language=request.language,
                unit_number=request.unit_number
            )

        if not exercises:
            raise ValidationError(
                f"No hay ejercicios para {request.language} unidad {request.unit_number}",
                field="unit_number"
            )

        # FIX Cortez52: Batch load all hints and tests to prevent N+1 queries
        exercise_ids = [e.id for e in exercises]
        all_hints_by_exercise = hint_repo.get_by_exercise_ids(exercise_ids)
        all_tests_by_exercise = test_repo.get_by_exercise_ids(exercise_ids)

        # Preparar ejercicios con hints y tests
        ejercicios_preparados = []
        tiempo_total = 0

        for exercise in exercises:
            # FIX Cortez52: Use pre-loaded data instead of per-exercise queries
            hints = all_hints_by_exercise.get(exercise.id, [])
            tests = all_tests_by_exercise.get(exercise.id, [])

            ejercicio_data = {
                'id': exercise.id,
                'titulo': exercise.title,
                'consigna': exercise.mission_markdown or exercise.description,
                'codigo_inicial': exercise.starter_code or "",
                'pistas': [h.content for h in sorted(hints, key=lambda x: x.hint_number)],
                'tests': [
                    {'input': t.input, 'expected': t.expected_output}
                    for t in sorted(tests, key=lambda x: x.test_number)
                ],
                'tiempo_min': exercise.time_min
            }
            ejercicios_preparados.append(ejercicio_data)
            tiempo_total += exercise.time_min

        # Crear sesión
        session_id = str(uuid.uuid4())
        ahora = datetime.now()

        sesion_data = {
            'user_id': current_user.id,
            'language': request.language,
            'unit': request.unit_number,
            'ejercicios': ejercicios_preparados,
            'ejercicio_actual_index': 0,
            'total_ejercicios': len(ejercicios_preparados),
            'inicio': ahora,
            'fin_estimado': ahora + timedelta(minutes=tiempo_total),
            'resultados': [],
            'pistas_usadas': 0,
            'finalizado': False
        }

        guardar_sesion(session_id, sesion_data)

        primer_ejercicio = ejercicios_preparados[0]

        return SesionEntrenamiento(
            session_id=session_id,
            materia=request.language.upper(),
            tema=f"Unidad {request.unit_number}",
            ejercicio_actual=EjercicioActual(
                numero=1,
                consigna=primer_ejercicio['consigna'],
                codigo_inicial=primer_ejercicio['codigo_inicial']
            ),
            total_ejercicios=len(ejercicios_preparados),
            ejercicios_completados=0,
            tiempo_limite_min=tiempo_total,
            inicio=ahora,
            fin_estimado=ahora + timedelta(minutes=tiempo_total)
        )

    except (ExerciseNotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error("Error iniciando entrenamiento: %s", e, exc_info=True)
        raise DatabaseOperationError("start_training", details=str(e))


@router.post("/pista", response_model=PistaResponse)
async def solicitar_pista(
    request: SolicitarPistaRequest,
    current_user: dict = Depends(get_current_user)  # FIX Cortez69 HIGH-API-002
):
    """
    Solicita una pista para el ejercicio actual
    """
    try:
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            raise SessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            raise AuthorizationError("No tienes permiso para acceder a esta sesión")

        index_actual = sesion['ejercicio_actual_index']
        ejercicio = sesion['ejercicios'][index_actual]

        if 'pistas' not in ejercicio or not ejercicio['pistas']:
            raise ValidationError("Este ejercicio no tiene pistas disponibles", field="hints")

        if request.numero_pista < 0 or request.numero_pista >= len(ejercicio['pistas']):
            raise ValidationError(
                f"Número de pista inválido. Disponibles: 0-{len(ejercicio['pistas']) - 1}",
                field="numero_pista"
            )

        if 'pistas_usadas' not in sesion:
            sesion['pistas_usadas'] = 0

        if request.numero_pista >= sesion['pistas_usadas']:
            sesion['pistas_usadas'] = request.numero_pista + 1
            guardar_sesion(request.session_id, sesion)
            logger.info("Pista %d solicitada. Total usadas: %d", request.numero_pista + 1, sesion['pistas_usadas'])

        pista = ejercicio['pistas'][request.numero_pista]

        return PistaResponse(
            contenido=pista,
            numero=request.numero_pista,
            total_pistas=len(ejercicio['pistas'])
        )

    except (SessionNotFoundError, AuthorizationError, ValidationError):
        raise
    except Exception as e:
        logger.error("Error obteniendo pista: %s", e, exc_info=True)
        raise DatabaseOperationError("get_hint", details=str(e))


@router.get("/exercises/{exercise_id}/details")
async def get_exercise_details(
    exercise_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_teacher_role)
):
    """
    Obtiene los detalles completos de un ejercicio (solo para admins/teachers)
    """
    try:
        exercise_repo = ExerciseRepository(db)
        hint_repo = ExerciseHintRepository(db)
        test_repo = ExerciseTestRepository(db)

        exercise = exercise_repo.get_by_id(exercise_id)
        if not exercise:
            raise ExerciseNotFoundError(exercise_id)

        hints = hint_repo.get_by_exercise(exercise_id)
        tests = test_repo.get_by_exercise(exercise_id)

        response = {
            "id": exercise.id,
            "subject_code": exercise.subject_code,
            "title": exercise.title,
            "description": exercise.description,
            "difficulty": exercise.difficulty,
            "time_min": exercise.time_min,
            "unit": exercise.unit,
            "language": exercise.language,
            "mission_markdown": exercise.mission_markdown,
            "story_markdown": exercise.story_markdown,
            "constraints": exercise.constraints,
            "starter_code": exercise.starter_code,
            "solution_code": exercise.solution_code,
            "tags": exercise.tags,
            "learning_objectives": exercise.learning_objectives,
            "cognitive_level": exercise.cognitive_level,
            "version": exercise.version,
            "is_active": exercise.is_active,
            "created_at": exercise.created_at.isoformat() if exercise.created_at else None,
            "updated_at": exercise.updated_at.isoformat() if exercise.updated_at else None,
            "hints": [
                {
                    "id": hint.id,
                    "hint_number": hint.hint_number,
                    "title": hint.title,
                    "content": hint.content,
                    "penalty_points": hint.penalty_points,
                }
                for hint in sorted(hints, key=lambda h: h.hint_number)
            ],
            "tests": [
                {
                    "id": test.id,
                    "test_number": test.test_number,
                    "description": test.description,
                    "input": test.input,
                    "expected_output": test.expected_output,
                    "is_hidden": test.is_hidden,
                    "timeout_seconds": test.timeout_seconds,
                }
                for test in sorted(tests, key=lambda t: t.test_number)
            ],
            "stats": {
                "total_hints": len(hints),
                "total_tests": len(tests),
                "hidden_tests": sum(1 for t in tests if t.is_hidden),
                "visible_tests": sum(1 for t in tests if not t.is_hidden),
            }
        }

        logger.info("Exercise details retrieved by teacher: %s", exercise_id)
        return response

    except ExerciseNotFoundError:
        raise
    except Exception as e:
        logger.error("Error getting exercise details for %s: %s", exercise_id, e, exc_info=True)
        raise DatabaseOperationError("get_exercise_details", details=str(e))


# =============================================================================
# Cortez56: Endpoints V1 Legacy (faltantes para compatibilidad con frontend)
# =============================================================================

@router.post("/submit-ejercicio")
async def submit_ejercicio(
    request: SubmitEjercicioRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # FIX Cortez69 HIGH-API-002
):
    """
    Cortez56: Endpoint V1 legacy para enviar código de un ejercicio.
    Evalúa el código contra los tests del ejercicio actual.

    Returns:
        - correcto: bool
        - tests_pasados / tests_totales
        - mensaje: feedback
        - siguiente_ejercicio: si hay más
        - resultado_final: si terminó la sesión
    """
    try:
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            raise SessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            raise AuthorizationError("No tienes permiso para acceder a esta sesión")

        if sesion.get('finalizado', False):
            raise ValidationError("Esta sesión ya ha finalizado", field="session_id")

        index_actual = sesion['ejercicio_actual_index']
        ejercicio = sesion['ejercicios'][index_actual]

        # Evaluar código usando CodeEvaluator
        evaluator = CodeEvaluator()
        tests = ejercicio.get('tests', [])

        if not tests:
            # Si no hay tests, evaluar si el código compila/ejecuta sin errores
            resultado = evaluator.evaluate_code(
                code=request.codigo_usuario,
                language=sesion.get('language', 'python')
            )
            tests_pasados = 1 if resultado.get('success', False) else 0
            tests_totales = 1
        else:
            # Evaluar contra tests definidos
            tests_pasados = 0
            tests_totales = len(tests)

            for test in tests:
                test_result = evaluator.run_test(
                    code=request.codigo_usuario,
                    language=sesion.get('language', 'python'),
                    test_input=test.get('input', ''),
                    expected_output=test.get('expected', '')
                )
                if test_result.get('passed', False):
                    tests_pasados += 1

        correcto = tests_pasados == tests_totales

        # Guardar resultado
        resultado_ejercicio = ResultadoEjercicio(
            numero=index_actual + 1,
            correcto=correcto,
            tests_pasados=tests_pasados,
            tests_totales=tests_totales,
            mensaje="¡Correcto!" if correcto else f"Pasaste {tests_pasados}/{tests_totales} tests"
        )

        sesion['resultados'].append(resultado_ejercicio.model_dump())

        response_data = {
            "correcto": correcto,
            "tests_pasados": tests_pasados,
            "tests_totales": tests_totales,
            "mensaje": resultado_ejercicio.mensaje,
            "siguiente_ejercicio": None,
            "resultado_final": None
        }

        if correcto:
            # Avanzar al siguiente ejercicio
            sesion['ejercicio_actual_index'] += 1

            if sesion['ejercicio_actual_index'] < sesion['total_ejercicios']:
                # Hay más ejercicios
                siguiente = sesion['ejercicios'][sesion['ejercicio_actual_index']]
                response_data["siguiente_ejercicio"] = EjercicioActual(
                    numero=sesion['ejercicio_actual_index'] + 1,
                    consigna=siguiente['consigna'],
                    codigo_inicial=siguiente['codigo_inicial']
                ).model_dump()
            else:
                # Sesión finalizada
                sesion['finalizado'] = True
                tiempo_usado = int((datetime.now() - sesion['inicio']).total_seconds() / 60)
                ejercicios_correctos = sum(1 for r in sesion['resultados'] if r['correcto'])
                porcentaje = (ejercicios_correctos / sesion['total_ejercicios']) * 100

                response_data["resultado_final"] = ResultadoFinal(
                    session_id=request.session_id,
                    nota_final=porcentaje / 10,  # Convertir a escala 0-10
                    ejercicios_correctos=ejercicios_correctos,
                    total_ejercicios=sesion['total_ejercicios'],
                    porcentaje=porcentaje,
                    aprobado=porcentaje >= 60,
                    tiempo_usado_min=tiempo_usado,
                    resultados_detalle=[ResultadoEjercicio(**r) for r in sesion['resultados']]
                ).model_dump()

        guardar_sesion(request.session_id, sesion)
        logger.info("Ejercicio %d evaluado: %s", index_actual + 1, "correcto" if correcto else "incorrecto")

        return response_data

    except (SessionNotFoundError, AuthorizationError, ValidationError):
        raise
    except Exception as e:
        logger.error("Error evaluando ejercicio: %s", e, exc_info=True)
        raise DatabaseOperationError("submit_exercise", details=str(e))


@router.post("/corregir-ia", response_model=CorreccionIAResponse)
async def corregir_con_ia(
    request: CorreccionIARequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # FIX Cortez69 HIGH-API-002,
    llm_provider = Depends(get_llm_provider)
):
    """
    Cortez56: Endpoint para solicitar corrección y sugerencias de la IA.
    Usa T-IA-Cog para analizar el código y dar feedback pedagógico.
    """
    try:
        sesion = obtener_sesion(request.session_id)
        if not sesion:
            raise SessionNotFoundError(request.session_id)

        if sesion['user_id'] != current_user.id:
            raise AuthorizationError("No tienes permiso para acceder a esta sesión")

        index_actual = sesion['ejercicio_actual_index']
        ejercicio = sesion['ejercicios'][index_actual]

        # Crear prompt para el LLM
        prompt = f"""Analiza el siguiente código de un estudiante y proporciona feedback pedagógico.

Ejercicio: {ejercicio['titulo']}
Consigna: {ejercicio['consigna']}

Código del estudiante:
```
{request.codigo_usuario}
```

Proporciona:
1. Un análisis breve del código (máximo 3 oraciones)
2. Lista de sugerencias de mejora (máximo 4)
3. NO proporciones el código corregido completo, solo indicaciones

Responde en formato JSON:
{{"analisis": "...", "sugerencias": ["...", "..."]}}
"""

        messages = [LLMMessage(role=LLMRole.USER, content=prompt)]

        try:
            response = await llm_provider.generate(messages, temperature=0.7)

            # Parsear respuesta JSON del LLM
            import json
            response_text = response.content if hasattr(response, 'content') else str(response)

            # Extraer JSON de la respuesta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(response_text[json_start:json_end])
                analisis = parsed.get('analisis', 'Análisis no disponible')
                sugerencias = parsed.get('sugerencias', [])
            else:
                analisis = response_text[:500]
                sugerencias = ["Revisa tu código paso a paso"]

        except Exception as llm_error:
            logger.warning("Error en LLM para corrección: %s", llm_error)
            # Fallback sin LLM
            analisis = "Tu código está siendo evaluado. Asegúrate de seguir las instrucciones del ejercicio."
            sugerencias = [
                "Verifica que tu código compile sin errores",
                "Comprueba que las variables estén bien definidas",
                "Revisa la lógica de tu algoritmo paso a paso"
            ]

        # Evaluar tests para obtener porcentaje
        evaluator = CodeEvaluator()
        tests = ejercicio.get('tests', [])
        tests_pasados = 0
        tests_totales = max(len(tests), 1)

        for test in tests:
            test_result = evaluator.run_test(
                code=request.codigo_usuario,
                language=sesion.get('language', 'python'),
                test_input=test.get('input', ''),
                expected_output=test.get('expected', '')
            )
            if test_result.get('passed', False):
                tests_pasados += 1

        porcentaje = (tests_pasados / tests_totales) * 100
        tiempo_usado = int((datetime.now() - sesion['inicio']).total_seconds() / 60)

        return CorreccionIAResponse(
            analisis=analisis,
            sugerencias=sugerencias[:4],  # Máximo 4 sugerencias
            codigo_corregido=None,  # No damos código corregido por políticas pedagógicas
            porcentaje=porcentaje,
            aprobado=porcentaje >= 60,
            tiempo_usado_min=tiempo_usado,
            resultados_detalle=[
                ResultadoEjercicio(
                    numero=index_actual + 1,
                    correcto=tests_pasados == tests_totales,
                    tests_pasados=tests_pasados,
                    tests_totales=tests_totales,
                    mensaje=f"Tests: {tests_pasados}/{tests_totales}"
                )
            ]
        )

    except (SessionNotFoundError, AuthorizationError):
        raise
    except Exception as e:
        logger.error("Error en corrección IA: %s", e, exc_info=True)
        raise DatabaseOperationError("ai_correction", details=str(e))


@router.get("/sesion/{session_id}/estado", response_model=SesionEntrenamientoExtendida)
async def obtener_estado_sesion(
    session_id: str,
    current_user: dict = Depends(get_current_user)  # FIX Cortez69 HIGH-API-002
):
    """
    Cortez56: Obtiene el estado actual de una sesión de entrenamiento.
    Incluye información extendida para N4 traceability.
    """
    try:
        sesion = obtener_sesion(session_id)
        if not sesion:
            raise SessionNotFoundError(session_id)

        if sesion['user_id'] != current_user.id:
            raise AuthorizationError("No tienes permiso para acceder a esta sesión")

        index_actual = sesion['ejercicio_actual_index']

        # Si ya finalizó, devolver el último ejercicio
        if sesion.get('finalizado', False) or index_actual >= len(sesion['ejercicios']):
            ejercicio = sesion['ejercicios'][-1]
            index_actual = len(sesion['ejercicios']) - 1
        else:
            ejercicio = sesion['ejercicios'][index_actual]

        return SesionEntrenamientoExtendida(
            session_id=session_id,
            materia=sesion.get('language', 'PYTHON').upper(),
            tema=f"Unidad {sesion.get('unit', 1)}",
            ejercicio_actual=EjercicioActual(
                numero=index_actual + 1,
                consigna=ejercicio['consigna'],
                codigo_inicial=ejercicio['codigo_inicial']
            ),
            total_ejercicios=sesion['total_ejercicios'],
            ejercicios_completados=len(sesion.get('resultados', [])),
            tiempo_limite_min=sum(e.get('tiempo_min', 15) for e in sesion['ejercicios']),
            inicio=sesion['inicio'],
            fin_estimado=sesion['fin_estimado'],
            # Campos extendidos Cortez50
            trace_sequence_id=sesion.get('trace_sequence_id'),
            pistas_disponibles=len(ejercicio.get('pistas', [])),
            pistas_usadas=sesion.get('pistas_usadas', 0),
            intentos_ejercicio_actual=sesion.get('intentos_actual', 0),
            estado_cognitivo_actual=sesion.get('estado_cognitivo'),
            riesgos_activos=sesion.get('riesgos_activos', []),
            feature_flags={
                "use_v2": sesion.get('use_v2', False),
                "n4_tracing": sesion.get('n4_tracing', True),
                "risk_monitor": sesion.get('risk_monitor', True)
            }
        )

    except (SessionNotFoundError, AuthorizationError):
        raise
    except Exception as e:
        logger.error("Error obteniendo estado de sesión %s: %s", session_id, e, exc_info=True)
        raise DatabaseOperationError("get_session_state", details=str(e))
