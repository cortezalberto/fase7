from fastapi import APIRouter, Depends, Request  # Cortez58: Removed unused HTTPException, status
from fastapi.security import OAuth2PasswordBearer
# FIX Cortez36: Import custom exception for consistent error handling
from backend.api.exceptions import ExerciseNotFoundError, DatabaseOperationError
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Set
import os
import json
import logging
from pathlib import Path
# FIX Cortez36: Import from shared utility module (consolidated from duplicate code)
from backend.utils.sandbox import execute_python_code

from backend.database.config import get_db
from backend.models.exercise import Exercise, UserExerciseSubmission
# FIX Cortez36: Import from deps.py instead of router-to-router import
from backend.api.deps import get_current_user
# FIX Cortez25: Use UserDB from database.models to avoid duplicate table definition
from backend.database.models import UserDB as User
from backend.llm.ollama_provider import OllamaProvider
# FIX 1.3 Cortez3: Import rate limiter for code execution endpoint
from backend.api.middleware.rate_limiter import limiter
# NUEVO: Importar loader de ejercicios JSON y evaluador Alex
from backend.data.exercises.loader import ExerciseLoader
from backend.services.code_evaluator import CodeEvaluator
# Importar LLM provider para evaluación con IA
from backend.api.deps import get_llm_provider
from backend.llm.base import LLMMessage, LLMRole
from backend.core.security import decode_access_token
from backend.api.schemas.exercises import (
    ExerciseJSONSchema,
    ExerciseListItemSchema,
    CodeSubmissionRequest,
    EvaluationResultSchema,
    SandboxResultSchema,
    SubmissionResponseSchema,
    ExerciseStatsSchema,
    UserProgressSchema,
    # Legacy schemas
    ExerciseResponse,
    CodeSubmission,
    SubmissionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exercises", tags=["Code Exercises"])

# Inicializar loader y evaluador
exercise_loader = ExerciseLoader()
# Code evaluator se inicializará con LLM provider en cada request

# FIX Cortez51: Optional OAuth2 scheme for optional authentication
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    FIX Cortez51: Get current user if authenticated, None otherwise.
    Used for endpoints that work both authenticated and unauthenticated.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def get_completed_exercise_ids(user: Optional[User], db: Session) -> Set[str]:
    """
    FIX Cortez51: Get set of exercise IDs completed by the user.
    Returns empty set if user is None.
    """
    if not user:
        return set()

    completed = db.query(UserExerciseSubmission.exercise_id).filter(
        UserExerciseSubmission.user_id == user.id,
        UserExerciseSubmission.is_correct == "true"
    ).distinct().all()

    return {row[0] for row in completed}


# Schemas
class ExerciseResponse(BaseModel):
    id: str
    title: str
    description: str
    difficulty_level: int
    starter_code: Optional[str]
    hints: Optional[List[str]]
    max_score: float
    time_limit_seconds: int


class CodeSubmission(BaseModel):
    exercise_id: str
    code: str


class SubmissionResult(BaseModel):
    id: str
    passed_tests: int
    total_tests: int
    is_correct: bool
    execution_time_ms: int
    ai_score: Optional[float]
    ai_feedback: Optional[str]
    code_quality_score: Optional[float]
    readability_score: Optional[float]
    efficiency_score: Optional[float]
    best_practices_score: Optional[float]
    test_results: List[Dict[str, Any]]


async def evaluate_code_with_ai(code: str, exercise: Exercise, test_results: dict) -> dict:
    """
    Evalúa el código usando Ollama para obtener feedback cualitativo
    """
    # Configurar Ollama con variables de entorno
    ollama_config = {
        "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
        "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
        "timeout": float(os.getenv("OLLAMA_TIMEOUT", "120"))
    }
    llm = OllamaProvider(ollama_config)
    
    prompt = f"""Eres un profesor de programación experto. Evalúa el siguiente código Python:

EJERCICIO: {exercise.title}
DESCRIPCIÓN: {exercise.description}
NIVEL: {exercise.difficulty_level}/10

CÓDIGO DEL ESTUDIANTE:
```python
{code}
```

RESULTADOS DE TESTS:
- Tests pasados: {test_results['passed']}/{test_results['total']}
- Tests correctos: {test_results['passed'] == test_results['total']}

Proporciona una evaluación detallada en formato JSON con:
{{
  "overall_score": <float 0-10>,
  "code_quality": <float 0-10>,
  "readability": <float 0-10>,
  "efficiency": <float 0-10>,
  "best_practices": <float 0-10>,
  "feedback": "<string con feedback constructivo>",
  "strengths": ["<fortaleza1>", "<fortaleza2>"],
  "improvements": ["<mejora1>", "<mejora2>"]
}}

RESPONDE SOLO CON EL JSON, SIN TEXTO ADICIONAL."""

    try:
        response = await llm.generate(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1000
        )
        
        # Parsear respuesta JSON
        content = response.content.strip()
        # Remover markdown si existe
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        evaluation = json.loads(content.strip())
        return evaluation
    except Exception as e:
        # FIX Cortez36: Use lazy logging formatting
        logger.warning("Error en evaluación de IA: %s", e, exc_info=True)
        # Fallback a evaluación básica
        base_score = (test_results['passed'] / test_results['total']) * 10 if test_results['total'] > 0 else 0
        return {
            "overall_score": base_score,
            "code_quality": base_score,
            "readability": base_score,
            "efficiency": base_score,
            "best_practices": base_score,
            "feedback": "Evaluación automática: " + ("Código correcto" if test_results['passed'] == test_results['total'] else "Hay errores en algunos tests"),
            "strengths": [],
            "improvements": []
        }


# =============================================================================
# NUEVOS ENDPOINTS - Sistema con Alex (Ejercicios JSON)
# =============================================================================

@router.get("/json/list", response_model=List[ExerciseListItemSchema])
async def list_json_exercises(
    difficulty: Optional[str] = None,
    unit: Optional[str] = None,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    framework: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista ejercicios del sistema JSON (con Alex evaluador)

    Parámetros:
    - difficulty: 'easy', 'medium', 'hard'
    - unit: 'unit1', 'unit2', etc.
    - tag: filtrar por tag específico
    - language: 'python', 'java'
    - framework: 'spring-boot'

    FIX Cortez51: Added optional authentication to check completed exercises
    """
    # Usar el método search mejorado del loader
    unit_num = None
    if unit:
        # Extraer número del unit (ej: 'unit1' -> 1)
        # FIX Cortez51: Log warning instead of silently ignoring invalid unit format
        try:
            unit_num = int(unit.replace('unit', '').replace('U', ''))
        except ValueError:
            logger.warning("Invalid unit format '%s', expected 'unit1', 'unit2', etc. Ignoring filter.", unit)

    tags_list = [tag] if tag else None

    exercises = exercise_loader.search(
        difficulty=difficulty,
        tags=tags_list,
        unit=unit_num,
        language=language,
        framework=framework
    )

    # FIX Cortez51: Get completed exercise IDs for current user
    completed_ids = get_completed_exercise_ids(current_user, db)

    # Convertir a schema de listado
    result = []
    for ex in exercises:
        result.append(ExerciseListItemSchema(
            id=ex['id'],
            title=ex['meta']['title'],
            difficulty=ex['meta']['difficulty'],
            estimated_time_minutes=ex['meta'].get('estimated_time_min', ex['meta'].get('estimated_time_minutes', 0)),
            points=ex['meta'].get('points', 0),
            tags=ex['meta']['tags'],
            is_completed=ex['id'] in completed_ids
        ))

    return result


@router.get("/json/stats")
async def get_json_exercises_stats():
    """Obtiene estadísticas de los ejercicios JSON incluyendo lenguaje y framework"""
    stats = exercise_loader.get_stats()
    
    # Retornar stats completas incluyendo by_language y by_framework
    return {
        "total_exercises": stats['total_exercises'],
        "by_difficulty": stats['by_difficulty'],
        "by_language": stats.get('by_language', {}),
        "by_framework": stats.get('by_framework', {}),
        "total_time_hours": stats['total_time_hours'],
        "unique_tags": stats['unique_tags']
    }


@router.get("/json/filters")
async def get_available_filters():
    """Obtiene los valores disponibles para todos los filtros"""
    return exercise_loader.get_available_filters()


@router.get("/json/{exercise_id}", response_model=ExerciseJSONSchema)
async def get_json_exercise(
    exercise_id: str
):
    """Obtiene un ejercicio específico del sistema JSON"""
    exercise = exercise_loader.get_by_id(exercise_id)
    
    if not exercise:
        # FIX Cortez53: Use custom exception
        raise ExerciseNotFoundError(exercise_id)
    
    return ExerciseJSONSchema(**exercise)


@router.post("/json/{exercise_id}/submit", response_model=EvaluationResultSchema)
@limiter.limit("10/minute")
async def submit_json_exercise(
    request: Request,
    exercise_id: str,
    submission: CodeSubmissionRequest,
    llm_provider = Depends(get_llm_provider)
):
    """
    Evalúa el código del estudiante con Alex (mentor IA)
    
    Flujo:
    1. Cargar ejercicio JSON
    2. Ejecutar código en sandbox
    3. Evaluar con Alex (CodeEvaluator)
    4. Retornar evaluación completa con XP y logros
    """
    # 1. Cargar ejercicio
    exercise = exercise_loader.get_by_id(exercise_id)
    if not exercise:
        # FIX Cortez36: Use custom exception for consistent error handling
        raise ExerciseNotFoundError(exercise_id)
    
    # 2. Ejecutar tests ocultos en sandbox SOLO si es Python
    # Para Java/Spring Boot, solo evaluación con IA
    language = exercise['meta'].get('language', 'python').lower()
    is_java = language == 'java' or 'spring' in exercise['meta'].get('framework', '').lower()
    
    # FIX Cortez36: Use lazy logging formatting
    logger.info("Ejercicio detectado: language=%s, is_java=%s", language, is_java)
    
    if is_java:
        # Java/Spring Boot: Solo evaluación con IA, sin ejecución
        logger.info("Ejercicio de Java/Spring Boot detectado - Solo evaluación con IA")
        sandbox_result = {
            "exit_code": -1,  # -1 indica "no ejecutado"
            "stdout": "[Java/Spring Boot] Este código no se ejecuta en sandbox Python. Evaluación solo por IA.",
            "stderr": "",
            "execution_time_ms": 0,
            "tests_passed": 0,
            "tests_total": len(exercise['hidden_tests']),
            "language": language,
            "evaluation_type": "ai_only"  # Indicador para que la IA sepa que no hay ejecución
        }
    else:
        # Python: Ejecución normal en sandbox
        # FIX Cortez36: Use lazy logging formatting
        logger.info("Ejecutando código para ejercicio %s (usuario anónimo)", exercise_id)
    
    # Ejecutar tests ocultos (solo para Python)
    tests_passed = 0
    tests_total = len(exercise['hidden_tests'])
    stdout_output = ""
    stderr_output = ""
    total_execution_time = 0
    
    if not is_java:  # Solo ejecutar si es Python
        for i, test in enumerate(exercise['hidden_tests'], 1):
            # Adaptarse a la estructura real de los JSON (input/expected)
            test_input = test.get('input', test.get('input_data', ''))
            if isinstance(test_input, dict) or isinstance(test_input, list):
                test_input = json.dumps(test_input)
            
            # Soportar tanto 'expected_output' (legacy) como 'expected' (nuevo)
            expected = test.get('expected_output') or test.get('expected', '')
            
            # FIX Cortez36: Use lazy logging formatting
            logger.info("Ejecutando test %d/%d: input='%s', expected='%s'", i, tests_total, test_input, expected)
            
            # Si expected es una expresión Python (ej: "total == 42600"), evaluarla
            if expected and ('==' in expected or 'and' in expected or 'or' in expected or '>' in expected or '<' in expected):
                # Es una expresión Python, ejecutar código y evaluar
                try:
                    # Crear contexto ejecutando el código del estudiante
                    exec_globals = {}
                    exec(submission.student_code, exec_globals)
                    
                    # Evaluar la expresión expected en ese contexto
                    test_passed = eval(expected, exec_globals)
                    
                    if test_passed:
                        tests_passed += 1
                        # FIX Cortez36: Use lazy logging formatting
                        logger.info("✓ Test %d PASADO: %s", i, expected)
                    else:
                        # FIX Cortez36: Use lazy logging formatting
                        logger.warning("✗ Test %d FALLÓ: %s (evaluó a False)", i, expected)
                except Exception as e:
                    # FIX Cortez36: Use lazy logging formatting
                    logger.warning("✗ Test %d ERROR: %s", i, e)
            else:
                # Es un test de output, ejecutar código con input
                stdout, stderr, exec_time = execute_python_code(
                    submission.student_code,
                    str(test_input),
                    timeout_seconds=30
                )
                
                total_execution_time += exec_time
                stdout_output += stdout + "\n"
                stderr_output += stderr + "\n"
                
                # Verificar si pasó el test
                if not stderr:
                    if expected:
                        # Comparar output
                        expected_str = str(expected).strip()
                        actual = stdout.strip()
                        if expected_str == actual:
                            tests_passed += 1
                            # FIX Cortez36: Use lazy logging formatting
                            logger.info("✓ Test %d PASADO: output coincide", i)
                        else:
                            # FIX Cortez36: Use lazy logging formatting
                            logger.warning("✗ Test %d FALLÓ: expected '%s' != actual '%s'", i, expected_str, actual)
                    else:
                        # No hay expected, solo verificar que no haya errores
                        tests_passed += 1
                        # FIX Cortez36: Use lazy logging formatting
                        logger.info("✓ Test %d PASADO: sin errores", i)
                else:
                    # FIX Cortez36: Use lazy logging formatting
                    logger.warning("✗ Test %d FALLÓ: %s", i, stderr)
        
        # Crear sandbox_result solo si es Python (si es Java ya se creó arriba)
        sandbox_result = {
            "exit_code": 0 if not stderr_output.strip() else 1,
            "stdout": stdout_output.strip(),
            "stderr": stderr_output.strip(),
            "execution_time_ms": total_execution_time,
            "tests_passed": tests_passed,
            "tests_total": tests_total,
            "language": "python",
            "evaluation_type": "execution"
        }
    
    # 3. Evaluar con Alex (IA)
    # FIX Cortez36: Use lazy logging formatting
    logger.info("Evaluando con Alex (IA): %d/%d tests pasados", tests_passed, tests_total)
    
    # Inicializar evaluador con LLM provider (Ollama)
    code_evaluator = CodeEvaluator(llm_client=llm_provider)
    
    evaluation = await code_evaluator.evaluate(
        exercise=exercise,
        student_code=submission.student_code,
        sandbox_result=sandbox_result
    )
    
    # 4. Guardar en BD (opcional, para historial)
    # TODO: Crear modelo UserExerciseEvaluation para guardar evaluaciones Alex

    # FIX Cortez36: Use lazy logging formatting
    logger.info("Evaluación completa: Score=%s, XP=%s", evaluation['evaluation']['score'], evaluation['gamification']['xp_earned'])
    
    return EvaluationResultSchema(**evaluation)


# =============================================================================
# LEGACY ENDPOINTS - Sistema de BD (compatibilidad hacia atrás)
# =============================================================================
async def list_exercises(
    difficulty: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los ejercicios disponibles"""
    query = db.query(Exercise)
    
    if difficulty is not None:
        query = query.filter(Exercise.difficulty_level == difficulty)
    
    exercises = query.order_by(Exercise.difficulty_level).all()
    
    return [
        {
            "id": ex.id,
            "title": ex.title,
            "description": ex.description,
            "difficulty_level": ex.difficulty_level,
            "starter_code": ex.starter_code,
            "hints": ex.hints,
            "max_score": ex.max_score,
            "time_limit_seconds": ex.time_limit_seconds
        }
        for ex in exercises
    ]


@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)  # FIX Cortez54: get_current_user returns dict
):
    """Obtiene estadísticas del usuario"""
    # FIX Cortez54: Access user_id from dict, not .id attribute
    user_id = current_user.get("user_id")
    submissions = db.query(UserExerciseSubmission).filter(
        UserExerciseSubmission.user_id == user_id
    ).all()
    
    if not submissions:
        return {
            "total_submissions": 0,
            "completed_exercises": 0,
            "average_score": 0.0,
            "total_exercises": 0
        }
    
    correct_count = sum(1 for s in submissions if s.is_correct == "true")
    scores = [s.ai_score for s in submissions if s.ai_score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    unique_exercises = len(set(s.exercise_id for s in submissions))
    
    return {
        "total_submissions": len(submissions),
        "completed_exercises": correct_count,
        "average_score": round(avg_score, 2),
        "total_exercises": unique_exercises
    }


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    exercise_id: str,
    db: Session = Depends(get_db)
):
    """Obtiene un ejercicio específico"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()

    if not exercise:
        # FIX Cortez36: Use custom exception for consistent error handling
        raise ExerciseNotFoundError(exercise_id)

    return {
        "id": exercise.id,
        "title": exercise.title,
        "description": exercise.description,
        "difficulty_level": exercise.difficulty_level,
        "starter_code": exercise.starter_code,
        "hints": exercise.hints,
        "max_score": exercise.max_score,
        "time_limit_seconds": exercise.time_limit_seconds
    }


@router.post("/submit", response_model=SubmissionResult)
@limiter.limit("5/minute")  # FIX 1.3 Cortez3: Rate limit code execution (DOS protection)
async def submit_code(
    request: Request,  # FIX 1.3 Cortez3: Required for rate limiter
    submission: CodeSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envía código para evaluación (requiere autenticación)"""
    # Obtener ejercicio
    exercise = db.query(Exercise).filter(Exercise.id == submission.exercise_id).first()

    if not exercise:
        # FIX Cortez36: Use custom exception for consistent error handling
        raise ExerciseNotFoundError(submission.exercise_id)

    # Ejecutar tests
    test_results = []
    passed_tests = 0
    total_tests = len(exercise.test_cases)
    total_execution_time = 0
    
    for i, test_case in enumerate(exercise.test_cases):
        test_input = test_case.get("input", "")
        expected_output = test_case.get("expected_output", "")
        
        output, error, exec_time = execute_python_code(
            submission.code,
            test_input,
            exercise.time_limit_seconds
        )
        
        total_execution_time += exec_time
        
        is_correct = output == expected_output and not error
        if is_correct:
            passed_tests += 1
        
        test_results.append({
            "test_number": i + 1,
            "input": test_input,
            "expected_output": expected_output,
            "actual_output": output,
            "error": error,
            "passed": is_correct,
            "execution_time_ms": exec_time
        })
    
    # Evaluar con IA
    ai_evaluation = await evaluate_code_with_ai(
        submission.code,
        exercise,
        {"passed": passed_tests, "total": total_tests}
    )
    
    # Guardar submission con el usuario autenticado
    new_submission = UserExerciseSubmission(
        user_id=current_user.id,
        exercise_id=exercise.id,
        submitted_code=submission.code,
        passed_tests=passed_tests,
        total_tests=total_tests,
        execution_time_ms=total_execution_time,
        ai_score=ai_evaluation.get("overall_score"),
        ai_feedback=json.dumps(ai_evaluation.get("feedback", "")),
        code_quality_score=ai_evaluation.get("code_quality"),
        readability_score=ai_evaluation.get("readability"),
        efficiency_score=ai_evaluation.get("efficiency"),
        best_practices_score=ai_evaluation.get("best_practices"),
        is_correct="true" if passed_tests == total_tests else "false"
    )
    
    # Cortez58: Add error handling for database commit
    try:
        db.add(new_submission)
        db.commit()
        db.refresh(new_submission)
    except Exception as e:
        db.rollback()
        logger.error("Failed to save submission: %s", str(e))
        raise DatabaseOperationError(operation="save_submission", details=str(e))

    return {
        "id": new_submission.id,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "is_correct": passed_tests == total_tests,
        "execution_time_ms": total_execution_time,
        "ai_score": ai_evaluation.get("overall_score"),
        "ai_feedback": json.dumps(ai_evaluation, ensure_ascii=False),
        "code_quality_score": ai_evaluation.get("code_quality"),
        "readability_score": ai_evaluation.get("readability"),
        "efficiency_score": ai_evaluation.get("efficiency"),
        "best_practices_score": ai_evaluation.get("best_practices"),
        "test_results": test_results
    }


@router.get("/user/submissions")
async def get_user_submissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene todas las submissions del usuario actual"""
    submissions = db.query(UserExerciseSubmission).filter(
        UserExerciseSubmission.user_id == current_user.id
    ).order_by(UserExerciseSubmission.submitted_at.desc()).all()
    
    return {
        "total": len(submissions),
        "submissions": [
            {
                "id": s.id,
                "exercise_id": s.exercise_id,
                "passed_tests": s.passed_tests,
                "total_tests": s.total_tests,
                "is_correct": s.is_correct,
                "ai_score": s.ai_score,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None
            }
            for s in submissions
        ]
    }
