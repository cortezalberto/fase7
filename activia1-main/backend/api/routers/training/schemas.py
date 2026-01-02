"""
Training Schemas - Pydantic models for Digital Training.

Cortez46: Extracted from training.py (1,620 lines)
Cortez50: Extended with N4 traceability and integration schemas
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class EjercicioInfo(BaseModel):
    """Información básica de un ejercicio"""
    id: str
    titulo: str
    dificultad: str
    tiempo_estimado_min: int
    puntos: int


class LeccionInfo(BaseModel):
    """Información de una lección con sus ejercicios"""
    id: str
    nombre: str
    descripcion: str
    unit_number: int
    ejercicios: List[EjercicioInfo]
    total_puntos: int
    dificultad: str  # Dificultad promedio de la lección


class LenguajeInfo(BaseModel):
    """Información de un lenguaje de programación con sus lecciones"""
    language: str
    nombre_completo: str
    lecciones: List[LeccionInfo]


# LEGACY SCHEMAS (mantener para compatibilidad)
class TemaInfo(BaseModel):
    """Información de un tema disponible (LEGACY)"""
    id: str
    nombre: str
    descripcion: str
    dificultad: str
    tiempo_estimado_min: int


class MateriaInfo(BaseModel):
    """Información de una materia con sus temas (LEGACY)"""
    materia: str
    codigo: str
    temas: List[TemaInfo]


class IniciarEntrenamientoRequest(BaseModel):
    """Request para iniciar una sesión de entrenamiento"""
    language: str  # "python", "java", etc.
    unit_number: int  # 1, 2, 3, etc.
    exercise_id: Optional[str] = None  # Opcional: ID de ejercicio específico (ej: "SEC-01")


class IniciarEntrenamientoRequestLegacy(BaseModel):
    """Request para iniciar una sesión de entrenamiento (LEGACY)"""
    materia_codigo: str
    tema_id: str


class EjercicioActual(BaseModel):
    """Ejercicio actual que el usuario está resolviendo"""
    numero: int
    consigna: str
    codigo_inicial: str


class SesionEntrenamiento(BaseModel):
    """Información de una sesión de entrenamiento activa"""
    session_id: str
    materia: str
    tema: str
    ejercicio_actual: EjercicioActual
    total_ejercicios: int
    ejercicios_completados: int
    tiempo_limite_min: int
    inicio: datetime
    fin_estimado: datetime


class SubmitEjercicioRequest(BaseModel):
    """Request para enviar el código de un ejercicio"""
    session_id: str
    codigo_usuario: str


class ResultadoEjercicio(BaseModel):
    """Resultado de un ejercicio individual"""
    numero: int
    correcto: bool
    tests_pasados: int
    tests_totales: int
    mensaje: str


class ResultadoFinal(BaseModel):
    """Resultado final del examen completo"""
    session_id: str
    nota_final: float
    ejercicios_correctos: int
    total_ejercicios: int
    porcentaje: float
    aprobado: bool
    tiempo_usado_min: int
    resultados_detalle: List[ResultadoEjercicio]


class SolicitarPistaRequest(BaseModel):
    """Request para solicitar una pista"""
    session_id: str
    numero_pista: int  # 0, 1 o 2


class PistaResponse(BaseModel):
    """Respuesta con una pista"""
    contenido: str
    numero: int
    total_pistas: int


class CorreccionIARequest(BaseModel):
    """Request para solicitar corrección con IA"""
    session_id: str
    codigo_usuario: str


class CorreccionIAResponse(BaseModel):
    """Respuesta con corrección y sugerencias de IA"""
    analisis: str
    sugerencias: List[str]
    codigo_corregido: Optional[str] = None
    porcentaje: float
    aprobado: bool
    tiempo_usado_min: int
    resultados_detalle: List[ResultadoEjercicio]


# =============================================================================
# CORTEZ50: N4 Traceability & Integration Schemas
# =============================================================================

class CognitiveStateEnum(str, Enum):
    """Estados cognitivos inferidos durante entrenamiento"""
    INICIO = "inicio"
    EXPLORACION = "exploracion"
    IMPLEMENTACION = "implementacion"
    DEPURACION = "depuracion"
    DEPURACION_SINTAXIS = "depuracion_sintaxis"
    CAMBIO_ESTRATEGIA = "cambio_estrategia"
    VALIDACION = "validacion"
    ESTANCAMIENTO = "estancamiento"
    REFLEXION = "reflexion"


class HelpLevelEnum(str, Enum):
    """Niveles de ayuda para pistas"""
    MINIMO = "minimo"
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class RiskTypeEnum(str, Enum):
    """Tipos de riesgo detectables"""
    COPY_PASTE = "copy_paste"
    FRUSTRATION = "frustration"
    HINT_DEPENDENCY = "hint_dependency"
    RAPID_SUBMISSION = "rapid_submission"
    TIME_PRESSURE = "time_pressure"
    COGNITIVE_OVERLOAD = "cognitive_overload"


class RiskSeverityEnum(str, Enum):
    """Severidad de riesgos"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# --- Pista V2 (con integracion T-IA-Cog) ---

class SolicitarPistaV2Request(BaseModel):
    """Request para solicitar pista contextual con T-IA-Cog"""
    session_id: str
    numero_pista: int = Field(..., ge=1, le=4, description="Nivel de pista (1-4)")
    codigo_actual: Optional[str] = Field(None, description="Codigo actual del estudiante")
    ultimo_error: Optional[str] = Field(None, description="Ultimo error encontrado")


class PistaV2Response(BaseModel):
    """Respuesta con pista contextual de T-IA-Cog"""
    contenido: str
    numero: int
    nivel_ayuda: HelpLevelEnum
    total_pistas: int = 4
    requiere_reflexion: bool = True
    pregunta_seguimiento: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Reflexion Post-Ejercicio ---

class ReflexionRequest(BaseModel):
    """Request para capturar reflexion post-ejercicio"""
    session_id: str
    exercise_id: str
    que_fue_dificil: str = Field(..., min_length=10, description="Que fue lo mas dificil")
    como_lo_resolvi: str = Field(..., min_length=10, description="Como lo resolviste")
    que_aprendi: str = Field(..., min_length=10, description="Que aprendiste")
    alternativas_consideradas: Optional[str] = Field(None, description="Alternativas que consideraste")
    errores_cometidos: Optional[str] = Field(None, description="Errores que cometiste y por que")


class ReflexionResponse(BaseModel):
    """Respuesta a la captura de reflexion"""
    trace_id: str
    mensaje: str
    dimension_cognitiva_inferida: str
    nivel_metacognitivo: str
    xp_bonus: int = 0


# --- Analisis de Proceso ---

class TraceResumen(BaseModel):
    """Resumen de una traza cognitiva"""
    timestamp: datetime
    tipo: str  # "code_attempt", "hint_request", "reflection"
    estado_cognitivo: CognitiveStateEnum
    confianza_inferencia: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskFlag(BaseModel):
    """Flag de riesgo detectado"""
    tipo: RiskTypeEnum
    severidad: RiskSeverityEnum
    mensaje: str
    detectado_en: datetime
    resuelto: bool = False


class ProcesoAnalisis(BaseModel):
    """Analisis del proceso cognitivo de una sesion"""
    session_id: str
    student_id: str
    total_trazas: int
    trazas_resumen: List[TraceResumen]
    estados_mas_frecuentes: List[str]
    transiciones_cognitivas: int
    cambios_estrategia: int
    tiempo_por_estado: Dict[str, int]
    riesgos_detectados: List[RiskFlag]
    indice_autonomia: float = Field(..., ge=0, le=1, description="0=dependiente, 1=autonomo")
    indice_reflexion: float = Field(..., ge=0, le=1, description="Nivel de reflexion demostrado")
    recomendaciones: List[str]


class ProcesoRequest(BaseModel):
    """Request para obtener analisis de proceso"""
    incluir_trazas: bool = True
    incluir_riesgos: bool = True
    incluir_recomendaciones: bool = True


# --- Resultado Extendido con Trazabilidad ---

class ResultadoEjercicioExtendido(BaseModel):
    """Resultado de ejercicio con datos de trazabilidad"""
    numero: int
    correcto: bool
    tests_pasados: int
    tests_totales: int
    mensaje: str
    # Cortez50: Campos de trazabilidad
    intentos_realizados: int = 0
    pistas_solicitadas: int = 0
    tiempo_ejercicio_segundos: int = 0
    estado_cognitivo_final: Optional[CognitiveStateEnum] = None
    riesgos_detectados: List[str] = Field(default_factory=list)
    trace_ids: List[str] = Field(default_factory=list)


class ResultadoFinalExtendido(BaseModel):
    """Resultado final con metricas de proceso"""
    session_id: str
    nota_final: float
    ejercicios_correctos: int
    total_ejercicios: int
    porcentaje: float
    aprobado: bool
    tiempo_usado_min: int
    resultados_detalle: List[ResultadoEjercicioExtendido]
    # Cortez50: Metricas de proceso
    metricas_proceso: Optional[Dict[str, Any]] = None
    indice_autonomia: Optional[float] = None
    reflexiones_capturadas: int = 0
    trace_sequence_id: Optional[str] = None


# --- Submit V2 con contexto adicional ---

class SubmitEjercicioV2Request(BaseModel):
    """Request extendido para enviar codigo con contexto"""
    session_id: str
    codigo_usuario: str
    tiempo_desde_ultimo_ms: Optional[int] = Field(None, description="Tiempo desde ultimo submit")
    es_codigo_pegado: Optional[bool] = Field(None, description="Si el codigo fue pegado vs escrito")


class SubmitEjercicioV2Response(BaseModel):
    """Respuesta extendida con datos de trazabilidad"""
    correcto: bool
    tests_pasados: int
    tests_totales: int
    mensaje: str
    siguiente_ejercicio: Optional[EjercicioActual] = None
    finalizado: bool = False
    resultado_final: Optional[ResultadoFinalExtendido] = None
    # Cortez50: Datos de traza
    trace_id: Optional[str] = None
    estado_cognitivo_inferido: Optional[CognitiveStateEnum] = None
    riesgos_activos: List[RiskFlag] = Field(default_factory=list)


# --- Sesion Extendida ---

class SesionEntrenamientoExtendida(BaseModel):
    """Sesion de entrenamiento con soporte para trazabilidad"""
    session_id: str
    materia: str
    tema: str
    ejercicio_actual: EjercicioActual
    total_ejercicios: int
    ejercicios_completados: int
    tiempo_limite_min: int
    inicio: datetime
    fin_estimado: datetime
    # Cortez50: Campos adicionales
    trace_sequence_id: Optional[str] = None
    pistas_disponibles: int = 4
    pistas_usadas: int = 0
    intentos_ejercicio_actual: int = 0
    estado_cognitivo_actual: Optional[CognitiveStateEnum] = None
    riesgos_activos: List[str] = Field(default_factory=list)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
