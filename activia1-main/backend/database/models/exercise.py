"""
Exercise Models - Programming exercises and related entities.

Cortez42: Extracted from monolithic models.py (1,772 lines)

Provides:
- ExerciseDB: Programming exercises
- ExerciseHintDB: Progressive hints with penalties
- ExerciseTestDB: Unit tests for exercises
- ExerciseAttemptDB: Student attempts
- ExerciseRubricCriterionDB: Rubric criteria
- RubricLevelDB: Achievement levels for rubrics
"""
from sqlalchemy import (
    Column, String, Text, Float, Integer, Boolean, DateTime,
    ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .base import Base, BaseModel, JSONBCompatible, utc_now


class ExerciseDB(Base, BaseModel):
    """
    Database model for programming exercises

    Ejercicios de programacion con consigna, codigo inicial, tests y pistas.
    Migracion desde backend/data/exercises/*.json y backend/data/training/*.json
    """

    __tablename__ = "exercises"

    # References
    subject_code = Column(String(50), ForeignKey("subjects.code", ondelete="CASCADE"), nullable=False, index=True)

    # Basic metadata
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False)  # 'Easy', 'Medium', 'Hard'
    time_min = Column(Integer, nullable=False)  # Tiempo estimado en minutos
    unit = Column(Integer, nullable=True)  # 1-7 (null for legacy exercises)
    language = Column(String(20), nullable=False)  # 'python', 'java'

    # Pedagogical content
    mission_markdown = Column(Text, nullable=False)  # Consigna completa
    story_markdown = Column(Text, nullable=True)  # Contexto/historia del ejercicio
    constraints = Column(JSON, default=list)  # Restricciones/requisitos como array

    # Code
    starter_code = Column(Text, nullable=False)  # Codigo inicial con TODOs
    solution_code = Column(Text, nullable=True)  # Solucion de referencia (NO enviar a frontend)

    # Pedagogical metadata
    tags = Column(JSONBCompatible, default=list)  # ['Variables', 'Condicionales']
    learning_objectives = Column(JSONBCompatible, default=list)  # Objetivos de aprendizaje
    cognitive_level = Column(String(20), nullable=True)  # 'Recordar', 'Comprender', 'Aplicar', etc.

    # Scoring (FASE 1.5)
    max_score = Column(Integer, default=100, nullable=False)  # Puntaje maximo del ejercicio

    # Versioning and state
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    subject = relationship("SubjectDB", back_populates="exercises")
    hints = relationship("ExerciseHintDB", back_populates="exercise", cascade="all, delete-orphan", order_by="ExerciseHintDB.hint_number")
    tests = relationship("ExerciseTestDB", back_populates="exercise", cascade="all, delete-orphan", order_by="ExerciseTestDB.test_number")
    attempts = relationship("ExerciseAttemptDB", back_populates="exercise", cascade="all, delete-orphan")
    rubric_criteria = relationship("ExerciseRubricCriterionDB", back_populates="exercise", cascade="all, delete-orphan", order_by="ExerciseRubricCriterionDB.display_order")

    # Indexes
    __table_args__ = (
        Index('idx_exercises_subject', 'subject_code'),
        Index('idx_exercises_unit', 'unit'),
        Index('idx_exercises_difficulty', 'difficulty'),
        Index('idx_exercises_language', 'language'),
        Index('idx_exercises_active', 'is_active'),
        Index('idx_exercises_tags', 'tags', postgresql_using='gin'),  # GIN index for JSONB
        CheckConstraint("difficulty IN ('Easy', 'Medium', 'Hard')", name='check_exercise_difficulty'),
        CheckConstraint("language IN ('python', 'java')", name='check_exercise_language'),
        CheckConstraint("time_min > 0", name='check_exercise_time_positive'),
    )


class ExerciseHintDB(Base, BaseModel):
    """
    Database model for exercise hints (pistas graduadas)

    Pistas con penalizacion creciente que se revelan una a una.
    """

    __tablename__ = "exercise_hints"

    # Reference to exercise
    exercise_id = Column(String(50), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)

    # Hint content
    hint_number = Column(Integer, nullable=False)  # 1, 2, 3, 4 (orden de revelacion)
    title = Column(String(200), nullable=True)  # "Estructura basica de validacion"
    content = Column(Text, nullable=False)  # Contenido de la pista

    # Penalty
    penalty_points = Column(Integer, default=0, nullable=False)  # 5, 10, 15, 20

    # Relationship
    exercise = relationship("ExerciseDB", back_populates="hints")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_hints_exercise', 'exercise_id'),
        Index('idx_hints_order', 'exercise_id', 'hint_number'),
        UniqueConstraint('exercise_id', 'hint_number', name='uq_exercise_hint_number'),
        CheckConstraint("hint_number > 0", name='check_hint_number_positive'),
        CheckConstraint("penalty_points >= 0", name='check_penalty_nonnegative'),
    )


class ExerciseTestDB(Base, BaseModel):
    """
    Database model for exercise unit tests

    Tests que el codigo del estudiante debe pasar.
    Pueden ser visibles (feedback durante desarrollo) u ocultos (evaluacion final).
    """

    __tablename__ = "exercise_tests"

    # Reference to exercise
    exercise_id = Column(String(50), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)

    # Test identification
    test_number = Column(Integer, nullable=False)  # Orden: 1, 2, 3...
    description = Column(Text, nullable=True)  # "Validacion de limites exactos"

    # Test data
    input = Column(Text, nullable=False)  # "validar_nota(85)"
    expected = Column(Text, nullable=False)  # "True" o "85.0"

    # Configuration
    is_hidden = Column(Boolean, default=False, nullable=False)  # TRUE = no visible al estudiante
    timeout_seconds = Column(Integer, default=5, nullable=False)

    # Relationship
    exercise = relationship("ExerciseDB", back_populates="tests")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_tests_exercise', 'exercise_id'),
        Index('idx_tests_hidden', 'exercise_id', 'is_hidden'),
        Index('idx_tests_order', 'exercise_id', 'test_number'),
        UniqueConstraint('exercise_id', 'test_number', name='uq_exercise_test_number'),
        CheckConstraint("test_number > 0", name='check_test_number_positive'),
        CheckConstraint("timeout_seconds > 0", name='check_timeout_positive'),
    )


class ExerciseAttemptDB(Base, BaseModel):
    """
    Database model for student exercise attempts

    Intentos de resolucion de ejercicios por parte de estudiantes.
    Permite tracking completo, analytics y trazabilidad N4.
    """

    __tablename__ = "exercise_attempts"

    # References
    exercise_id = Column(String(50), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String(100), nullable=False, index=True)
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True, index=True)

    # Submitted code
    submitted_code = Column(Text, nullable=False)

    # Execution results
    tests_passed = Column(Integer, default=0, nullable=False)
    tests_total = Column(Integer, default=0, nullable=False)
    score = Column(Float, nullable=True)  # 0-10 scale
    status = Column(String(20), nullable=False)  # 'PASS', 'FAIL', 'ERROR', 'TIMEOUT'

    # Execution details
    execution_time_ms = Column(Integer, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)

    # AI feedback (from CodeEvaluator)
    ai_feedback_summary = Column(Text, nullable=True)  # Resumen corto para toast
    ai_feedback_detailed = Column(Text, nullable=True)  # Markdown completo
    ai_suggestions = Column(JSONBCompatible, default=list)  # Array de sugerencias

    # Rubric evaluation (FASE 1.5)
    rubric_evaluation = Column(JSONBCompatible, default=dict, nullable=True)
    # Formato: {
    #   "criteria": [
    #     {
    #       "criterion_name": "Funcionalidad",
    #       "level_achieved": "Bueno",
    #       "score": 8.0,
    #       "points": 80,
    #       "feedback": "Implementa la mayoria de casos correctamente..."
    #     }
    #   ],
    #   "total_score_rubric": 85.0,  # Antes de penalizaciones
    #   "penalty_from_hints": 15,
    #   "final_score": 70.0  # total_score_rubric - penalty
    # }

    # Hints usage
    hints_used = Column(Integer, default=0, nullable=False)
    penalty_applied = Column(Integer, default=0, nullable=False)  # Penalizacion total

    # Attempt metadata
    attempt_number = Column(Integer, default=1, nullable=False)  # 1er, 2do, 3er intento
    submitted_at = Column(DateTime, default=utc_now, nullable=False)

    # Relationships
    exercise = relationship("ExerciseDB", back_populates="attempts")
    session = relationship("SessionDB")

    # Indexes for analytics
    __table_args__ = (
        Index('idx_attempts_exercise', 'exercise_id'),
        Index('idx_attempts_student', 'student_id'),
        Index('idx_attempts_session', 'session_id'),
        Index('idx_attempts_status', 'status'),
        Index('idx_attempts_submitted', 'submitted_at'),
        # Composite index for student progress queries
        Index('idx_attempts_student_exercise', 'student_id', 'exercise_id', 'submitted_at'),
        CheckConstraint("status IN ('PASS', 'FAIL', 'ERROR', 'TIMEOUT')", name='check_attempt_status'),
        CheckConstraint("score IS NULL OR (score >= 0 AND score <= 10)", name='check_score_range'),
        CheckConstraint("tests_passed >= 0 AND tests_passed <= tests_total", name='check_tests_valid'),
        CheckConstraint("hints_used >= 0", name='check_hints_nonnegative'),
        CheckConstraint("attempt_number > 0", name='check_attempt_number_positive'),
    )


class ExerciseRubricCriterionDB(Base, BaseModel):
    """
    Database model for exercise rubric criteria (FASE 1.5)

    Criterios de evaluacion de un ejercicio con sus niveles de logro.
    Cada ejercicio tiene multiples criterios (Funcionalidad, Calidad, Robustez)
    y cada criterio tiene 4 niveles (Excelente, Bueno, Regular, Insuficiente).

    Ejemplos de criterios:
    - Funcionalidad (40%): Resuelve el problema correctamente?
    - Calidad de codigo (30%): Es legible, mantiene buenas practicas?
    - Robustez (30%): Maneja casos edge, errores?
    """

    __tablename__ = "exercise_rubric_criteria"

    # Reference to exercise
    exercise_id = Column(String(50), ForeignKey("exercises.id", ondelete="CASCADE"), nullable=False, index=True)

    # Criterion metadata
    criterion_name = Column(String(100), nullable=False)  # "Funcionalidad", "Calidad de codigo", etc.
    description = Column(Text, nullable=True)  # Descripcion detallada del criterio
    weight = Column(Float, nullable=False)  # 0.0-1.0 (ej: 0.4 = 40%)
    display_order = Column(Integer, nullable=False)  # Orden de presentacion (1, 2, 3...)

    # Relationships
    exercise = relationship("ExerciseDB", back_populates="rubric_criteria")
    levels = relationship("RubricLevelDB", back_populates="criterion", cascade="all, delete-orphan", order_by="RubricLevelDB.min_score.desc()")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_rubric_criteria_exercise', 'exercise_id'),
        Index('idx_rubric_criteria_order', 'exercise_id', 'display_order'),
        UniqueConstraint('exercise_id', 'criterion_name', name='uq_exercise_criterion_name'),
        UniqueConstraint('exercise_id', 'display_order', name='uq_exercise_criterion_order'),
        CheckConstraint("weight >= 0 AND weight <= 1", name='check_criterion_weight_range'),
        CheckConstraint("display_order > 0", name='check_criterion_order_positive'),
    )


class RubricLevelDB(Base, BaseModel):
    """
    Database model for rubric criterion levels (FASE 1.5)

    Niveles de logro para un criterio de rubrica.
    Cada criterio tiene 4 niveles estandar:
    - Excelente (9.0-10.0): Cumplimiento excepcional
    - Bueno (7.0-8.9): Cumplimiento satisfactorio
    - Regular (5.0-6.9): Cumplimiento basico
    - Insuficiente (0.0-4.9): No cumple o cumple parcialmente

    Ejemplo para criterio "Funcionalidad":
    - Excelente: "Implementa todos los casos correctamente, incluidos edge cases"
    - Bueno: "Implementa la mayoria de casos, falta algunos edge cases"
    - Regular: "Implementa casos basicos, falla en casos intermedios"
    - Insuficiente: "No implementa correctamente o no funciona"
    """

    __tablename__ = "rubric_levels"

    # Reference to criterion
    criterion_id = Column(String(36), ForeignKey("exercise_rubric_criteria.id", ondelete="CASCADE"), nullable=False, index=True)

    # Level metadata
    level_name = Column(String(50), nullable=False)  # "Excelente", "Bueno", "Regular", "Insuficiente"
    description = Column(Text, nullable=False)  # Que debe cumplir para alcanzar este nivel
    min_score = Column(Float, nullable=False)  # 9.0, 7.0, 5.0, 0.0
    max_score = Column(Float, nullable=False)  # 10.0, 8.9, 6.9, 4.9
    points = Column(Integer, nullable=False)  # Puntos otorgados si alcanza este nivel (0-100)

    # Relationship
    criterion = relationship("ExerciseRubricCriterionDB", back_populates="levels")

    # Indexes and constraints
    __table_args__ = (
        Index('idx_rubric_levels_criterion', 'criterion_id'),
        Index('idx_rubric_levels_score_range', 'criterion_id', 'min_score', 'max_score'),
        CheckConstraint("min_score >= 0 AND max_score <= 10", name='check_level_score_range'),
        CheckConstraint("min_score < max_score", name='check_level_score_order'),
        CheckConstraint("level_name IN ('Excelente', 'Bueno', 'Regular', 'Insuficiente')", name='check_level_name_valid'),
        CheckConstraint("points >= 0 AND points <= 100", name='check_level_points_range'),
    )
