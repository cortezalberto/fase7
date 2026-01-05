"""
Deep Diagnostics - Heavyweight Health Checks

Cortez66: Extracted from health.py
FIX Cortez74: Added rate limiting to prevent abuse

Endpoints:
- GET /health/deep: Comprehensive health check with metrics

Note: This endpoint is slower than probe endpoints.
Do NOT use for Kubernetes liveness/readiness probes.
"""
import logging
import time
import os
import sys
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.core.constants import utc_now
from ...deps import get_db
from ...schemas.common import APIResponse
from ...middleware.rate_limiter import limiter
from .utils import get_process_memory_mb, get_gc_stats

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/deep",
    response_model=APIResponse[dict],
    summary="Deep Health Check",
    description="""
    Health check exhaustivo con métricas detalladas.

    **ADVERTENCIA**: Este endpoint es más lento que /health porque ejecuta
    múltiples verificaciones. No usar para liveness/readiness probes.

    Verifica:
    - Latencias de PostgreSQL, Redis, LLM
    - Uso del pool de conexiones
    - Estadísticas de cache
    - Estadísticas de Prometheus metrics
    - Versiones de dependencias
    - Memoria del proceso

    **Uso recomendado**:
    - Monitoring dashboards (Grafana)
    - Troubleshooting manual
    - Alertas de degradación de performance
    """,
    responses={
        200: {"description": "Service is healthy (all checks passed)"},
        503: {"description": "Service is unhealthy or degraded"},
    },
)
@limiter.limit("30/minute")  # FIX Cortez74: More restrictive for deep check (expensive)
async def deep_health_check(
    request: Request,  # FIX Cortez74: Required for rate limiter
    db: Session = Depends(get_db),
) -> APIResponse[dict]:
    """
    Deep health check con métricas exhaustivas.

    Args:
        db: Sesión de base de datos (inyectada)

    Returns:
        APIResponse: Estado detallado del sistema
    """
    from backend import __version__, __author__

    checks: Dict[str, Any] = {}
    overall_healthy = True

    # 1. System Info
    checks["system"] = {
        "version": __version__,
        "author": __author__,
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "environment": os.getenv("ENVIRONMENT", "unknown"),
    }

    # 2. Database - Latencia + Pool Stats
    try:
        start_time = time.time()
        db_url = str(db.get_bind().url)
        is_sqlite = "sqlite" in db_url.lower()

        if is_sqlite:
            result = db.execute(text("SELECT sqlite_version()"))
            row = result.fetchone()
            db_version = f"SQLite {row[0]}" if row else "SQLite (unknown version)"
        else:
            result = db.execute(text("SELECT version()"))
            row = result.fetchone()
            db_version = row[0] if row else "unknown"

        db_latency_ms = round((time.time() - start_time) * 1000, 2)

        # Pool stats
        pool_size = None
        pool_checked_out = None
        pool_type = None
        try:
            pool = db.get_bind().pool
            pool_type = type(pool).__name__
            if hasattr(pool, 'size'):
                pool_size = pool.size()
            if hasattr(pool, 'checkedout'):
                pool_checked_out = pool.checkedout()
        except (AttributeError, TypeError) as e:
            logger.debug("Pool stats not available: %s", e)

        checks["database"] = {
            "status": "healthy",
            "latency_ms": db_latency_ms,
            "version": db_version[:50],
            "pool_type": pool_type,
            "pool_size": pool_size,
            "pool_checked_out": pool_checked_out,
            "pool_usage_percent": round((pool_checked_out / pool_size) * 100, 1) if pool_size and pool_checked_out else None,
        }

        if db_latency_ms > 100:
            checks["database"]["warning"] = "High latency detected"
            overall_healthy = False

        if pool_size and pool_checked_out and (pool_checked_out / pool_size) > 0.8:
            checks["database"]["warning"] = "Pool usage > 80%"
            overall_healthy = False

    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)[:100]}
        overall_healthy = False
        logger.error("Database deep check failed", exc_info=True)

    # 3. Redis - Latencia + Write/Read Test + Stats
    redis_client = None
    try:
        redis_url = os.getenv("REDIS_URL")

        if redis_url:
            import redis
            import uuid
            redis_client = redis.from_url(redis_url, decode_responses=True)

            # Test latencia con PING
            start_time = time.time()
            redis_client.ping()
            ping_latency_ms = round((time.time() - start_time) * 1000, 2)

            # Write/Read test
            test_key = f"health_check_{uuid.uuid4().hex[:8]}"
            test_value = f"test_{utc_now().isoformat()}"

            start_time = time.time()
            redis_client.setex(test_key, 10, test_value)
            write_latency_ms = round((time.time() - start_time) * 1000, 2)

            start_time = time.time()
            read_value = redis_client.get(test_key)
            read_latency_ms = round((time.time() - start_time) * 1000, 2)

            redis_client.delete(test_key)
            write_read_ok = read_value == test_value

            # Info stats
            info = redis_client.info()

            checks["redis"] = {
                "status": "healthy" if write_read_ok else "degraded",
                "ping_latency_ms": ping_latency_ms,
                "write_latency_ms": write_latency_ms,
                "read_latency_ms": read_latency_ms,
                "write_read_test": "passed" if write_read_ok else "failed",
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "uptime_days": round(info.get("uptime_in_seconds", 0) / 86400, 1),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            }

            # Calculate hit rate
            hits = info.get("keyspace_hits", 0)
            misses = info.get("keyspace_misses", 0)
            if hits + misses > 0:
                checks["redis"]["hit_rate_percent"] = round((hits / (hits + misses)) * 100, 1)

            # Alerts
            if ping_latency_ms > 50:
                checks["redis"]["warning"] = "High ping latency detected"
            if write_latency_ms > 100:
                checks["redis"]["warning"] = "High write latency detected"
            if not write_read_ok:
                checks["redis"]["error"] = "Write/read test failed"
                overall_healthy = False

        else:
            checks["redis"] = {"status": "not_configured"}

    except ImportError:
        checks["redis"] = {"status": "not_available", "note": "redis package not installed"}
    except Exception as e:
        checks["redis"] = {"status": "degraded", "error": str(e)[:100]}
        logger.warning("Redis deep check failed", extra={"error": str(e)})
    finally:
        if redis_client is not None:
            try:
                redis_client.close()
            except Exception as close_error:
                logger.debug("Failed to close Redis client in deep check: %s", close_error)

    # 4. Cache Stats
    try:
        from backend.core.cache import get_llm_cache

        llm_cache_enabled = os.getenv("LLM_CACHE_ENABLED", "true").lower() == "true"

        if llm_cache_enabled:
            cache = get_llm_cache()
            stats = cache.get_stats()

            checks["cache"] = {
                "status": "enabled",
                "hits": stats.get("hits"),
                "misses": stats.get("misses"),
                "hit_rate": round(stats.get("hit_rate", 0), 2),
                "size": stats.get("size"),
                "max_entries": cache.max_entries,
            }

            if stats.get("hit_rate", 0) < 50 and (stats.get("hits", 0) + stats.get("misses", 0)) > 10:
                checks["cache"]["warning"] = "Low hit rate detected"
        else:
            checks["cache"] = {"status": "disabled"}

    except Exception as e:
        checks["cache"] = {"status": "error", "error": str(e)[:100]}
        logger.warning("Cache stats check failed", extra={"error": str(e)})

    # 5. Process Memory & GC Stats
    checks["process"] = {
        "memory_mb": get_process_memory_mb(),
        "gc_stats": get_gc_stats(),
        "pid": os.getpid(),
    }

    memory_mb = checks["process"]["memory_mb"]
    if memory_mb and memory_mb > 500:
        checks["process"]["warning"] = f"High memory usage: {memory_mb}MB"

    # 6. Prometheus Metrics Stats
    try:
        from backend.api.monitoring.metrics import _metrics

        if _metrics:
            interactions_total = 0
            try:
                for metric in _metrics.get("interactions_total", {})._metrics.values():
                    interactions_total += metric._value.get()
            except Exception as e:
                logger.debug("Failed to collect interactions_total metric: %s", str(e))

            checks["metrics"] = {
                "status": "enabled",
                "interactions_total": int(interactions_total),
                "metrics_count": len(_metrics),
            }
        else:
            checks["metrics"] = {"status": "not_initialized"}

    except Exception as e:
        checks["metrics"] = {"status": "error", "error": str(e)[:100]}

    # 7. LLM Provider Status with Validation
    try:
        llm_provider = os.getenv("LLM_PROVIDER", "mock")

        checks["llm_provider"] = {
            "provider": llm_provider,
            "status": "configured" if llm_provider != "mock" else "mock",
        }

        if llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "")
            checks["llm_provider"]["api_key_configured"] = bool(api_key)
            checks["llm_provider"]["model"] = os.getenv("OPENAI_MODEL", "gpt-4")

            if api_key:
                try:
                    import openai
                    start_time = time.time()
                    client = openai.OpenAI(api_key=api_key)
                    models = list(client.models.list())[:1]
                    llm_latency_ms = round((time.time() - start_time) * 1000, 2)
                    checks["llm_provider"]["status"] = "healthy"
                    checks["llm_provider"]["latency_ms"] = llm_latency_ms
                    checks["llm_provider"]["api_validated"] = True

                    if llm_latency_ms > 2000:
                        checks["llm_provider"]["warning"] = "High LLM API latency"
                except ImportError:
                    checks["llm_provider"]["api_validated"] = False
                    checks["llm_provider"]["note"] = "openai package not installed"
                except Exception as e:
                    checks["llm_provider"]["status"] = "degraded"
                    checks["llm_provider"]["api_validated"] = False
                    checks["llm_provider"]["api_error"] = str(e)[:100]
                    logger.warning("OpenAI API validation failed", extra={"error": str(e)})

        elif llm_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY", "")
            checks["llm_provider"]["api_key_configured"] = bool(api_key)
            checks["llm_provider"]["model"] = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

            if api_key:
                try:
                    import google.generativeai as genai
                    start_time = time.time()
                    genai.configure(api_key=api_key)
                    models = list(genai.list_models())[:1]
                    llm_latency_ms = round((time.time() - start_time) * 1000, 2)
                    checks["llm_provider"]["status"] = "healthy"
                    checks["llm_provider"]["latency_ms"] = llm_latency_ms
                    checks["llm_provider"]["api_validated"] = True

                    if llm_latency_ms > 2000:
                        checks["llm_provider"]["warning"] = "High LLM API latency"
                except ImportError:
                    checks["llm_provider"]["api_validated"] = False
                    checks["llm_provider"]["note"] = "google-generativeai package not installed"
                except Exception as e:
                    checks["llm_provider"]["status"] = "degraded"
                    checks["llm_provider"]["api_validated"] = False
                    checks["llm_provider"]["api_error"] = str(e)[:100]
                    logger.warning("Gemini API validation failed", extra={"error": str(e)})

    except Exception as e:
        checks["llm_provider"] = {"status": "error", "error": str(e)[:100]}

    # Response
    if overall_healthy:
        return APIResponse(
            success=True,
            data={
                "status": "healthy",
                "checks": checks,
                "timestamp": utc_now().isoformat(),
            },
            message="All health checks passed"
        )
    else:
        return APIResponse(
            success=False,
            data={
                "status": "degraded",
                "checks": checks,
                "timestamp": utc_now().isoformat(),
            },
            message="Service is degraded"
        )
