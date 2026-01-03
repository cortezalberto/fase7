"""
Training Schemas - Backward Compatibility Wrapper

Cortez66: This file re-exports from the centralized schemas location.
Import from here or from backend.api.schemas.training - both work.

Original implementation moved to: backend/api/schemas/training.py
"""

# Re-export everything from the centralized location
from ...schemas.training import (
    # Basic info schemas
    EjercicioInfo,
    LeccionInfo,
    LenguajeInfo,
    TemaInfo,
    MateriaInfo,
    # Session schemas
    IniciarEntrenamientoRequest,
    IniciarEntrenamientoRequestLegacy,
    EjercicioActual,
    SesionEntrenamiento,
    SesionEntrenamientoExtendida,
    # Submit schemas
    SubmitEjercicioRequest,
    SubmitEjercicioV2Request,
    SubmitEjercicioV2Response,
    ResultadoEjercicio,
    ResultadoEjercicioExtendido,
    ResultadoFinal,
    ResultadoFinalExtendido,
    # Hint schemas
    SolicitarPistaRequest,
    PistaResponse,
    SolicitarPistaV2Request,
    PistaV2Response,
    # Cortez50: V2 Integration schemas
    HelpLevelEnum,
    CognitiveStateEnum,
    RiskTypeEnum,
    RiskSeverityEnum,
    RiskFlag,
    CognitiveInferenceData,
    ProcesoAnalisis,
    ReflexionRequest,
    ReflexionResponse,
    ProcesoResponse,
    # AI Correction
    CorreccionIAResponse,
)

__all__ = [
    # Basic info
    "EjercicioInfo",
    "LeccionInfo",
    "LenguajeInfo",
    "TemaInfo",
    "MateriaInfo",
    # Session
    "IniciarEntrenamientoRequest",
    "IniciarEntrenamientoRequestLegacy",
    "EjercicioActual",
    "SesionEntrenamiento",
    "SesionEntrenamientoExtendida",
    # Submit
    "SubmitEjercicioRequest",
    "SubmitEjercicioV2Request",
    "SubmitEjercicioV2Response",
    "ResultadoEjercicio",
    "ResultadoEjercicioExtendido",
    "ResultadoFinal",
    "ResultadoFinalExtendido",
    # Hint
    "SolicitarPistaRequest",
    "PistaResponse",
    "SolicitarPistaV2Request",
    "PistaV2Response",
    # V2 Integration
    "HelpLevelEnum",
    "CognitiveStateEnum",
    "RiskTypeEnum",
    "RiskSeverityEnum",
    "RiskFlag",
    "CognitiveInferenceData",
    "ProcesoAnalisis",
    "ReflexionRequest",
    "ReflexionResponse",
    "ProcesoResponse",
    # AI Correction
    "CorreccionIAResponse",
]
