"""
Session Storage - Redis and memory session management for training.

Cortez46: Extracted from training.py (1,620 lines)
FIX Cortez67: Implemented bounded memory cache with TTL to prevent memory leaks.
"""

import asyncio
import json
import logging
import os
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple

import redis

logger = logging.getLogger(__name__)

# Configuration constants
MAX_MEMORY_SESSIONS = int(os.getenv("TRAINING_MAX_MEMORY_SESSIONS", "1000"))
SESSION_TTL_HOURS = int(os.getenv("TRAINING_SESSION_TTL_HOURS", "24"))

# Configurar Redis para sesiones
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    redis_client.ping()
    logger.info("Redis conectado para sesiones de training")
    USE_REDIS = True
except Exception as e:
    logger.warning("Redis no disponible, usando memoria: %s", e)
    USE_REDIS = False
    redis_client = None


class BoundedSessionCache:
    """
    FIX Cortez67: Thread-safe bounded session cache with TTL.

    Features:
    - Maximum size limit (evicts oldest entries when full)
    - TTL-based expiration
    - LRU-like ordering (most recently accessed at end)
    - Async lock for thread safety
    """

    def __init__(
        self,
        max_size: int = MAX_MEMORY_SESSIONS,
        ttl_hours: int = SESSION_TTL_HOURS
    ):
        self._cache: OrderedDict[str, Tuple[datetime, Dict[str, Any]]] = OrderedDict()
        self._max_size = max_size
        self._ttl = timedelta(hours=ttl_hours)
        self._lock = asyncio.Lock()
        logger.info(
            "BoundedSessionCache initialized: max_size=%d, ttl_hours=%d",
            max_size, ttl_hours
        )

    async def set(self, session_id: str, datos: Dict[str, Any]) -> None:
        """Store session data with timestamp."""
        async with self._lock:
            # Remove if already exists (will re-add at end)
            if session_id in self._cache:
                del self._cache[session_id]

            # Evict oldest entries if at capacity
            while len(self._cache) >= self._max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                logger.debug("Evicted oldest session from memory cache: %s", oldest_key)

            # Add new entry at end (most recent)
            # FIX Cortez68 (MEDIUM): Use timezone-aware datetime
            self._cache[session_id] = (datetime.now(timezone.utc), datos)

    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if exists and not expired."""
        async with self._lock:
            if session_id not in self._cache:
                return None

            created, datos = self._cache[session_id]

            # Check TTL
            # FIX Cortez68 (MEDIUM): Use timezone-aware datetime
            if datetime.now(timezone.utc) - created > self._ttl:
                del self._cache[session_id]
                logger.debug("Session expired in memory cache: %s", session_id)
                return None

            # Move to end (mark as recently accessed)
            self._cache.move_to_end(session_id)
            return datos

    async def delete(self, session_id: str) -> bool:
        """Delete session from cache."""
        async with self._lock:
            if session_id in self._cache:
                del self._cache[session_id]
                return True
            return False

    async def keys(self) -> List[str]:
        """Get all non-expired session IDs."""
        async with self._lock:
            # FIX Cortez68 (MEDIUM): Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            return [
                k for k, (created, _) in self._cache.items()
                if now - created <= self._ttl
            ]

    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        async with self._lock:
            # FIX Cortez68 (MEDIUM): Use timezone-aware datetime
            now = datetime.now(timezone.utc)
            expired = [
                k for k, (created, _) in self._cache.items()
                if now - created > self._ttl
            ]
            for k in expired:
                del self._cache[k]

            if expired:
                logger.info("Cleaned up %d expired memory sessions", len(expired))
            return len(expired)

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# FIX Cortez67: Replace unbounded dict with bounded cache
_sesiones_memoria = BoundedSessionCache()


# Sync wrapper for backward compatibility with existing code
def _get_sync_from_memory(session_id: str) -> Optional[Dict[str, Any]]:
    """Sync wrapper for memory cache get (for use in sync functions)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _sesiones_memoria.get(session_id))
                return future.result(timeout=5.0)
        else:
            return asyncio.run(_sesiones_memoria.get(session_id))
    except Exception as e:
        logger.warning("Error getting session from memory cache: %s", e)
        return None


def _set_sync_to_memory(session_id: str, datos: Dict[str, Any]) -> None:
    """Sync wrapper for memory cache set (for use in sync functions)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule as a task if loop is running
            asyncio.create_task(_sesiones_memoria.set(session_id, datos))
        else:
            asyncio.run(_sesiones_memoria.set(session_id, datos))
    except Exception as e:
        logger.warning("Error setting session in memory cache: %s", e)


# Legacy dict alias for any direct access (should not be used)
sesiones_memoria: Dict[str, Dict[str, Any]] = {}


def guardar_sesion(session_id: str, datos: Dict[str, Any]) -> None:
    """Guarda una sesión en Redis o memoria (FIX Cortez67: uses bounded cache)."""
    # Convertir datetime a string para JSON
    datos_serializables = datos.copy()
    if 'inicio' in datos_serializables and isinstance(datos_serializables['inicio'], datetime):
        datos_serializables['inicio'] = datos_serializables['inicio'].isoformat()
    if 'fin_estimado' in datos_serializables and isinstance(datos_serializables['fin_estimado'], datetime):
        datos_serializables['fin_estimado'] = datos_serializables['fin_estimado'].isoformat()

    if USE_REDIS and redis_client:
        try:
            # Guardar en Redis con TTL de 2 horas
            redis_client.setex(
                f"training_session:{session_id}",
                7200,  # 2 horas
                json.dumps(datos_serializables)
            )
            logger.info("Sesion %s guardada en Redis", session_id)
        except Exception as e:
            logger.error("Error guardando en Redis: %s", e, exc_info=True)
            # FIX Cortez67: Use bounded cache instead of unbounded dict
            _set_sync_to_memory(session_id, datos)
    else:
        # FIX Cortez67: Use bounded cache instead of unbounded dict
        _set_sync_to_memory(session_id, datos)


def obtener_sesion(session_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene una sesión de Redis o memoria (FIX Cortez67: uses bounded cache)."""
    if USE_REDIS and redis_client:
        try:
            datos_json = redis_client.get(f"training_session:{session_id}")
            if datos_json:
                datos = json.loads(datos_json)
                # Convertir strings de datetime de vuelta a datetime
                if 'inicio' in datos and isinstance(datos['inicio'], str):
                    datos['inicio'] = datetime.fromisoformat(datos['inicio'])
                if 'fin_estimado' in datos and isinstance(datos['fin_estimado'], str):
                    datos['fin_estimado'] = datetime.fromisoformat(datos['fin_estimado'])
                logger.info("Sesion %s recuperada de Redis", session_id)
                return datos
        except Exception as e:
            logger.error("Error obteniendo de Redis: %s", e, exc_info=True)

    # FIX Cortez67: Use bounded cache instead of unbounded dict
    return _get_sync_from_memory(session_id)


def listar_sesiones_activas() -> List[str]:
    """Lista los IDs de sesiones activas (FIX Cortez67: async cache)."""
    if USE_REDIS and redis_client:
        try:
            keys = redis_client.keys("training_session:*")
            return [k.replace("training_session:", "") for k in keys]
        except Exception as e:
            logger.warning("Redis keys() failed, falling back to in-memory storage: %s", e)
    # FIX Cortez67: Use async bounded cache
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Return empty list if we can't access async cache synchronously
            return []
        return asyncio.run(_sesiones_memoria.keys())
    except Exception:
        return []


def eliminar_sesion(session_id: str) -> bool:
    """Elimina una sesión de Redis o memoria (FIX Cortez67: async cache)."""
    if USE_REDIS and redis_client:
        try:
            result = redis_client.delete(f"training_session:{session_id}")
            if result:
                logger.info("Sesion %s eliminada de Redis", session_id)
                return True
        except Exception as e:
            logger.error("Error eliminando de Redis: %s", e, exc_info=True)

    # FIX Cortez67: Use async bounded cache
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(_sesiones_memoria.delete(session_id))
            return True
        return asyncio.run(_sesiones_memoria.delete(session_id))
    except Exception:
        return False


# FIX Cortez67: Export cleanup function for use by background tasks
async def cleanup_expired_memory_sessions() -> int:
    """Clean up expired sessions from memory cache. Returns count of removed."""
    return await _sesiones_memoria.cleanup_expired()


def get_memory_cache_stats() -> Dict[str, Any]:
    """Get memory cache statistics for monitoring."""
    return {
        "size": _sesiones_memoria.size(),
        "max_size": _sesiones_memoria._max_size,
        "ttl_hours": SESSION_TTL_HOURS,
    }
