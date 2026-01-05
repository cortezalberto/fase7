"""
Configuración compartida para la API

Centraliza todas las configuraciones de la aplicación FastAPI,
leyendo valores desde variables de entorno con valores por defecto seguros.
"""
import os
from typing import List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()


# =============================================================================
# Configuración de Paginación
# =============================================================================

from ..core.constants import (
    DEFAULT_PAGE_SIZE as _DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE as _MAX_PAGE_SIZE,
    MIN_PAGE_SIZE as _MIN_PAGE_SIZE,
)

DEFAULT_PAGE_SIZE = _DEFAULT_PAGE_SIZE
MAX_PAGE_SIZE = _MAX_PAGE_SIZE
MIN_PAGE_SIZE = _MIN_PAGE_SIZE


# =============================================================================
# Configuración de CORS
# =============================================================================

def get_allowed_origins() -> List[str]:
    """
    Obtiene la lista de orígenes permitidos para CORS desde variable de entorno.

    Variable de entorno: ALLOWED_ORIGINS
    Formato: URLs separadas por comas
    Ejemplo: "http://localhost:3000,http://localhost:5173,https://app.example.com"

    Returns:
        List[str]: Lista de orígenes permitidos

    Note:
        En desarrollo, se permiten localhost en puertos comunes (3000, 5173, 8080).
        En producción, DEBE configurarse ALLOWED_ORIGINS con los dominios reales.
    """
    origins_env = os.getenv(
        "ALLOWED_ORIGINS",
        # Valores por defecto para desarrollo local (incluye puerto 3001 del frontend)
        "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://localhost:8080"
    )

    # Split por comas y limpiar espacios
    origins = [origin.strip() for origin in origins_env.split(",") if origin.strip()]

    # FIX Cortez69 CRIT-CORE-001: Use lazy logging
    logger.info("CORS allowed origins configured: %d origins", len(origins))

    return origins


# Lista de orígenes permitidos (calculada al importar el módulo)
CORS_ALLOWED_ORIGINS = get_allowed_origins()


# =============================================================================
# Configuración de Rate Limiting
# =============================================================================

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))


# =============================================================================
# Configuración de Timeouts
# =============================================================================

REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
DB_QUERY_TIMEOUT_SECONDS = int(os.getenv("DB_QUERY_TIMEOUT_SECONDS", "10"))

# FIX Cortez84 CRIT-GW-001: Centralize LLM timeout configuration
# Timeout for LLM API calls (prevents indefinite hangs)
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30.0"))


# =============================================================================
# Configuración de Seguridad
# =============================================================================

# Secret key para JWT (REQUERIDO - sin default inseguro)
# FIXED (2025-11-21): Eliminado default inseguro. Ahora DEBE configurarse.
SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError(
        "SECURITY ERROR: SECRET_KEY environment variable is REQUIRED.\n"
        "Generate a secure random key with:\n"
        "  python -c 'import secrets; print(secrets.token_urlsafe(32))'\n"
        "Then set it in your .env file:\n"
        "  SECRET_KEY=<generated_key>"
    )

# Validar longitud mínima (prevenir claves débiles)
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        f"SECURITY ERROR: SECRET_KEY must be at least 32 characters long.\n"
        f"Current length: {len(SECRET_KEY)} characters.\n"
        f"Generate a new one with:\n"
        f"  python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )


# =============================================================================
# Configuración de Entorno
# =============================================================================

# Detectar si estamos en producción
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT.lower() == "production"

# Modo debug (NUNCA debe estar en True en producción)
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# =============================================================================
# Cortez50: Feature Flags for Training Integration
# =============================================================================

# Flag to enable T-IA-Cog contextual hints generation
# When True: Uses LLM to generate pedagogically contextualized hints
# When False: Falls back to static hints from exercise definitions
TRAINING_USE_TUTOR_HINTS = os.getenv("TRAINING_USE_TUTOR_HINTS", "false").lower() == "true"

# Flag to enable N4 cognitive traceability in training mode
# When True: Records cognitive traces for each code attempt, hint request, and reflection
# When False: Training mode operates without traceability (lighter, faster)
TRAINING_N4_TRACING = os.getenv("TRAINING_N4_TRACING", "false").lower() == "true"

# Flag to enable real-time risk monitoring during training
# When True: Detects copy-paste, frustration, hint dependency in real-time
# When False: No risk analysis during training
TRAINING_RISK_MONITOR = os.getenv("TRAINING_RISK_MONITOR", "false").lower() == "true"

# Log feature flag status on startup
logger.info(
    "Training feature flags: TUTOR_HINTS=%s, N4_TRACING=%s, RISK_MONITOR=%s",
    TRAINING_USE_TUTOR_HINTS, TRAINING_N4_TRACING, TRAINING_RISK_MONITOR
)


# =============================================================================
# LTI 1.3 Configuration (HU-SYS-010)
# =============================================================================
# NOTE: LTI router is NOT enabled by default. To enable:
# 1. Set LTI_ENABLED=true in .env
# 2. Add router to main.py: app.include_router(lti.router, prefix="/api/v1/lti")

# Master switch for LTI integration
LTI_ENABLED = os.getenv("LTI_ENABLED", "false").lower() == "true"

# LTI state/nonce expiration (security parameters)
LTI_STATE_EXPIRATION_MINUTES = int(os.getenv("LTI_STATE_EXPIRATION_MINUTES", "10"))
LTI_NONCE_EXPIRATION_HOURS = int(os.getenv("LTI_NONCE_EXPIRATION_HOURS", "1"))

# JWKS cache TTL (how long to cache platform's public keys)
LTI_JWKS_CACHE_TTL_SECONDS = int(os.getenv("LTI_JWKS_CACHE_TTL_SECONDS", "3600"))

# Frontend URL for LTI redirects (after successful launch)
LTI_FRONTEND_URL = os.getenv("LTI_FRONTEND_URL", "http://localhost:3000")

# RSA key paths for signing our own tokens (for LTI Advantage/AGS)
# These are optional - only needed if implementing grade passback
LTI_PRIVATE_KEY_PATH = os.getenv("LTI_PRIVATE_KEY_PATH", "")
LTI_PUBLIC_KEY_PATH = os.getenv("LTI_PUBLIC_KEY_PATH", "")

# Log LTI configuration status
if LTI_ENABLED:
    logger.info(
        "LTI 1.3 integration: ENABLED (frontend: %s)",
        LTI_FRONTEND_URL
    )
else:
    logger.info("LTI 1.3 integration: DISABLED (set LTI_ENABLED=true to enable)")


# =============================================================================
# Función de Validación
# =============================================================================

def validate_production_config() -> None:
    """
    Valida que la configuración sea segura para el entorno de producción.

    Raises:
        RuntimeError: Si la configuración no es segura para producción
    """
    if not IS_PRODUCTION:
        return  # Solo validar en producción

    errors = []

    # Validar SECRET_KEY
    if SECRET_KEY == "dev-secret-key-change-in-production":
        errors.append(
            "Cannot run in production with default SECRET_KEY! "
            "Set SECRET_KEY environment variable."
        )

    # Validar CORS
    if any("localhost" in origin for origin in CORS_ALLOWED_ORIGINS):
        errors.append(
            "Cannot run in production with localhost in ALLOWED_ORIGINS! "
            "Set ALLOWED_ORIGINS environment variable with production domains."
        )

    # Validar DEBUG
    if DEBUG:
        errors.append(
            "Cannot run in production with DEBUG=true! "
            "Debug mode exposes stack traces and internal errors. "
            "Set DEBUG=false or remove DEBUG environment variable."
        )

    # Si hay errores, fallar rápido
    if errors:
        error_msg = "Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)