"""
FIX Cortez34: TypedDict definitions to replace Dict[str, Any] usage.

This module provides typed dictionaries for common data structures
to improve type safety across the codebase.
"""
from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict, NotRequired


# =============================================================================
# Student Profile TypedDicts
# =============================================================================

class StudentProfileDict(TypedDict, total=False):
    """
    TypedDict for student profile data.

    Used in: TutorInteractRequest.student_profile
    """
    level: str  # "novato", "intermedio", "avanzado"
    previous_topics: List[str]
    learning_style: str
    difficulty_preference: str
    language: str
    academic_program: str


# =============================================================================
# Context TypedDicts
# =============================================================================

class InteractionContextDict(TypedDict, total=False):
    """
    TypedDict for interaction context.

    Used in: TutorInteractRequest.context, CreateTutorSessionRequest.initial_context
    """
    current_exercise: str
    attempts: int
    learning_objective: str
    difficulty: str
    topic: str
    code_snippet: str
    error_message: str


class TraceContextDict(TypedDict, total=False):
    """
    TypedDict for trace context.

    Used in: CognitiveTraceCreate.context, CognitiveTraceResponse.context
    """
    topic: str
    exercise_id: str
    step_number: int
    code: str
    error: str
    ai_response: str
    user_input: str


# =============================================================================
# Metadata TypedDicts
# =============================================================================

class TraceMetadataDict(TypedDict, total=False):
    """
    TypedDict for trace metadata.

    Used in: CognitiveTraceCreate.trace_metadata, CognitiveTraceResponse.trace_metadata
    """
    tokens: int
    model: str
    processing_time_ms: int
    trace_id: str
    blocked: bool
    strategy_change: bool
    strategy_change_description: str


class TutorResponseMetadataDict(TypedDict, total=False):
    """
    TypedDict for tutor response metadata.

    Used in: TutorInteractResponse.metadata
    """
    trace_id: str
    processing_time_ms: int
    model: str
    tokens_used: int
    flow_id: str


# =============================================================================
# N4 Dimension TypedDicts
# =============================================================================

class SemanticUnderstandingDict(TypedDict, total=False):
    """
    TypedDict for semantic understanding dimension (N4).

    Used in: CognitiveTraceCreate.semantic_understanding
    """
    conceptos_clave: List[str]
    relaciones: List[str]
    nivel_comprension: str
    terminos_tecnico: List[str]


class CognitiveReasoningDict(TypedDict, total=False):
    """
    TypedDict for cognitive reasoning dimension (N4).

    Used in: CognitiveTraceCreate.cognitive_reasoning
    """
    razonamiento: str
    tipo_razonamiento: str  # "deductivo", "inductivo", "analogico"
    nivel_abstraccion: str
    complejidad_estimada: float


class AlgorithmicEvolutionDict(TypedDict, total=False):
    """
    TypedDict for algorithmic evolution dimension (N4).

    Used in: CognitiveTraceCreate.algorithmic_evolution
    """
    algoritmo_actual: str
    cambios_desde_anterior: List[str]
    complejidad_temporal: str
    complejidad_espacial: str


class EthicalRiskDataDict(TypedDict, total=False):
    """
    TypedDict for ethical/risk data dimension (N4).

    Used in: CognitiveTraceCreate.ethical_risk_data
    """
    riesgos_detectados: List[str]
    nivel_riesgo_global: str
    justificacion_requerida: bool
    uso_ia_excesivo: bool


class InteractionalDataDict(TypedDict, total=False):
    """
    TypedDict for interactional data dimension (N4).

    Used in: CognitiveTraceCreate.interactional_data
    """
    tipo_interaccion: str
    duracion_segundos: int
    numero_intercambios: int
    tono_conversacion: str


class ProcessDataDict(TypedDict, total=False):
    """
    TypedDict for process data dimension (N4).

    Used in: CognitiveTraceCreate.process_data
    """
    fase_actual: str
    transiciones: List[str]
    tiempo_en_fase_segundos: int
    bloqueos_detectados: int


# =============================================================================
# Distribution TypedDicts
# =============================================================================

class SemaforoDistributionDict(TypedDict, total=False):
    """
    TypedDict for semaforo distribution.

    Used in: TutorSessionAnalytics.semaforo_distribution
    """
    verde: int
    amarillo: int
    rojo: int


# =============================================================================
# Git Trace TypedDicts
# =============================================================================

class GitFileChangeDict(TypedDict):
    """
    TypedDict for git file change data.

    Used in: GitTrace.files_changed
    """
    filename: str
    change_type: str  # "added", "modified", "deleted"
    additions: int
    deletions: int
    patch: NotRequired[str]


# =============================================================================
# Risk TypedDicts
# =============================================================================

class RiskMetadataDict(TypedDict, total=False):
    """
    TypedDict for risk metadata.

    Used in: Risk schemas
    """
    detected_by: str
    detection_method: str
    confidence: float
    trace_ids: List[str]
    related_risks: List[str]


class RiskThresholdsDict(TypedDict, total=False):
    """
    TypedDict for risk thresholds configuration.

    Used in: PolicyConfig.risk_thresholds
    """
    ai_dependency: float
    lack_justification: float
    cognitive_delegation: float
    superficial_reasoning: float
