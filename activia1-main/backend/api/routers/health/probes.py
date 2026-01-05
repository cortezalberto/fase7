"""
Kubernetes Probes - Lightweight Health Checks

Cortez66: Extracted from health.py
FIX Cortez74: Added rate limiting to prevent abuse

Endpoints:
- GET /health: Basic health check with agent status
- GET /health/ping: Minimal ping endpoint
- GET /health/live: Kubernetes liveness probe
- GET /health/ready: Kubernetes readiness probe
"""
import logging
import time
import os
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from backend.core.constants import utc_now
from backend.database.repositories import SessionRepository
from ...deps import get_db, get_session_repository
from ...schemas.common import HealthStatus, APIResponse
from ...middleware.rate_limiter import limiter, get_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=HealthStatus,
    summary="Health Check",
    description="Verifica el estado de salud del servicio y sus componentes",
)
@limiter.limit(get_rate_limit("health"))  # FIX Cortez74: Add rate limiting
async def health_check(
    request: Request,  # FIX Cortez74: Required for rate limiter
    db: Session = Depends(get_db),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> HealthStatus:
    """
    Endpoint de health check que verifica:
    - Estado general del servicio
    - Conectividad con la base de datos
    - Estado de los agentes AI

    Returns:
        HealthStatus: Estado de salud del servicio
    """
    from backend import __version__

    # Verificar conexión a base de datos
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except OperationalError as e:
        logger.warning("Database connection error", exc_info=True, extra={"error": str(e)})
        db_status = "disconnected"
    except ProgrammingError as e:
        logger.error("Database query error", exc_info=True, extra={"error": str(e)})
        db_status = "disconnected"
    except Exception as e:
        logger.critical("Unexpected database error in health check", exc_info=True, extra={"error": str(e)})
        db_status = "disconnected"

    # Estado de agentes (mock para MVP)
    agents_status = {
        "T-IA-Cog": "operational",
        "E-IA-Proc": "operational",
        "S-IA-X": "operational",
        "AR-IA": "operational",
        "GOV-IA": "operational",
        "TC-N4": "operational",
    }

    # Determinar estado general
    if db_status == "connected" and all(
        status == "operational" for status in agents_status.values()
    ):
        overall_status = "healthy"
    elif db_status == "connected":
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthStatus(
        status=overall_status,
        version=__version__,
        database=db_status,
        agents=agents_status,
        timestamp=utc_now(),
    )


@router.get(
    "/ping",
    response_model=APIResponse[dict],
    summary="Simple Ping",
    description="Endpoint simple para verificar que el servicio está respondiendo.",
)
@limiter.limit(get_rate_limit("health"))  # FIX Cortez74: Add rate limiting
async def ping(request: Request) -> APIResponse[dict]:  # FIX Cortez74: Request for rate limiter
    """
    Endpoint minimalista para health checks externos.

    Returns:
        APIResponse con {"status": "ok", "timestamp": ...}
    """
    return APIResponse(
        success=True,
        data={
            "status": "ok",
            "timestamp": utc_now().isoformat(),
        },
        message="Service is responding",
    )


@router.get(
    "/live",
    response_model=APIResponse[dict],
    summary="Liveness Probe",
    description="""
    Kubernetes liveness probe - Verifica que el proceso está vivo.

    **Uso en Kubernetes**:
    ```yaml
    livenessProbe:
      httpGet:
        path: /api/v1/health/live
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
    ```
    """,
    responses={
        200: {"description": "Service is alive"},
        503: {"description": "Service is dead - restart required"},
    },
)
@limiter.limit(get_rate_limit("health"))  # FIX Cortez74: Add rate limiting
async def liveness_probe(request: Request) -> APIResponse[dict]:  # FIX Cortez74: Request for limiter
    """
    Liveness probe para Kubernetes.

    Returns:
        APIResponse: 200 si el proceso está vivo
    """
    return APIResponse(
        success=True,
        data={
            "status": "alive",
            "timestamp": utc_now().isoformat(),
        },
        message="Service is alive"
    )


@router.get(
    "/ready",
    response_model=APIResponse[dict],
    summary="Readiness Probe",
    description="""
    Kubernetes readiness probe - Verifica que el servicio está listo para recibir tráfico.

    Verifica:
    - PostgreSQL está accesible
    - Redis está accesible (si configurado)
    - LLM provider está accesible (opcional)

    **Uso en Kubernetes**:
    ```yaml
    readinessProbe:
      httpGet:
        path: /api/v1/health/ready
        port: 8000
      initialDelaySeconds: 20
      periodSeconds: 10
    ```
    """,
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is NOT ready"},
    },
)
@limiter.limit(get_rate_limit("health"))  # FIX Cortez74: Add rate limiting
async def readiness_probe(
    request: Request,  # FIX Cortez74: Required for rate limiter
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """
    Readiness probe para Kubernetes.

    Args:
        db: Sesión de base de datos (inyectada)

    Returns:
        APIResponse: 200 si listo, success=False si no listo
    """
    checks: Dict[str, Any] = {}
    is_ready = True

    # 1. Check PostgreSQL
    try:
        start_time = time.time()
        db.execute(text("SELECT 1"))
        db_latency_ms = round((time.time() - start_time) * 1000, 2)
        checks["database"] = {
            "status": "ready",
            "latency_ms": db_latency_ms,
        }
    except Exception as e:
        checks["database"] = {
            "status": "not_ready",
            "error": str(e)[:100],
        }
        is_ready = False
        logger.error("Database not ready in readiness probe", exc_info=True)

    # 2. Check Redis (optional)
    redis_client = None
    try:
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            import redis
            redis_client = redis.from_url(redis_url, decode_responses=True)

            start_time = time.time()
            redis_client.ping()
            redis_latency_ms = round((time.time() - start_time) * 1000, 2)

            checks["redis"] = {
                "status": "ready",
                "latency_ms": redis_latency_ms,
            }
        else:
            checks["redis"] = {"status": "not_configured"}
    except Exception as e:
        checks["redis"] = {
            "status": "not_ready",
            "error": str(e)[:100],
        }
        logger.warning("Redis not ready in readiness probe", extra={"error": str(e)})
    finally:
        if redis_client is not None:
            try:
                redis_client.close()
            except Exception as close_error:
                logger.debug("Failed to close Redis client: %s", close_error)

    # 3. Check LLM Provider
    try:
        llm_provider = os.getenv("LLM_PROVIDER", "mock")

        if llm_provider == "mock":
            checks["llm_provider"] = {"status": "ready", "provider": "mock"}
        else:
            checks["llm_provider"] = {"status": "configured", "provider": llm_provider}
    except Exception as e:
        checks["llm_provider"] = {"status": "error", "error": str(e)[:100]}
        logger.warning("LLM provider check failed", extra={"error": str(e)})

    # Response
    if is_ready:
        return APIResponse(
            success=True,
            data={
                "status": "ready",
                "checks": checks,
                "timestamp": utc_now().isoformat(),
            },
            message="Service is ready"
        )
    else:
        return APIResponse(
            success=False,
            data={
                "status": "not_ready",
                "checks": checks,
                "timestamp": utc_now().isoformat(),
            },
            message="Service is not ready"
        )
