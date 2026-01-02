"""
LLM Response Cache - Sistema de caché para respuestas de LLM

Implementa un cache en memoria con TTL para reducir costos de llamadas a LLM
al reutilizar respuestas para prompts idénticos o similares.

En producción, este módulo debería usar Redis para:
- Persistencia entre reinicios
- Compartir cache entre múltiples instancias
- Mayor capacidad de almacenamiento
"""
import hashlib
import json
import time
import logging
import threading
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from collections import OrderedDict

from .constants import (
    DEFAULT_CACHE_MAX_SIZE,
    DEFAULT_CACHE_TTL_SECONDS,
    CACHE_CLEANUP_INTERVAL_SECONDS,
)

# Prometheus metrics instrumentation (HIGH-01)
# Lazy import to avoid circular dependency with api.monitoring
# FIX Cortez33: Added thread-safe double-checked locking
_metrics_module = None
_metrics_lock = threading.Lock()


def _get_metrics():
    """
    Lazy load metrics module to avoid circular imports.

    FIX Cortez33: Thread-safe implementation using double-checked locking pattern.
    This prevents race conditions when multiple threads try to initialize
    the metrics module simultaneously.
    """
    global _metrics_module
    if _metrics_module is None:
        with _metrics_lock:
            # Double-check inside lock to avoid race condition
            if _metrics_module is None:
                try:
                    from ..api.monitoring import metrics as m
                    _metrics_module = m
                except ImportError:
                    _metrics_module = False  # Mark as unavailable
    return _metrics_module if _metrics_module else None

logger = logging.getLogger(__name__)


def _sanitize_for_logs(text: str, max_length: int = 20) -> str:
    """
    Sanitiza texto para logging seguro, ocultando PII potencial.

    Muestra solo un hash parcial del contenido para evitar exponer:
    - Información personal del estudiante
    - Detalles sensibles de código
    - Datos confidenciales

    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima de caracteres a mostrar (default: 20)

    Returns:
        Texto sanitizado con hash parcial

    Example:
        >>> _sanitize_for_logs("Mi nombre es Juan y mi email es juan@example.com")
        '[content_hash:e8d95a52...]'
    """
    if not text:
        return "[empty]"

    # Generar hash SHA-256 del contenido
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]

    # Mostrar solo longitud y hash parcial
    return f"[content_hash:{content_hash}, length:{len(text)}]"


class LRUCache:
    """
    LRU (Least Recently Used) Cache implementation.

    Mantiene un límite de tamaño y elimina las entradas menos
    recientemente usadas cuando se alcanza la capacidad máxima.
    """

    def __init__(self, max_size: int = 1000):
        """
        Inicializa el cache LRU.

        Args:
            max_size: Número máximo de entradas en cache
        """
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()  # Thread-safety para operaciones concurrentes

    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache y lo mueve al final (más reciente).
        Thread-safe.

        Args:
            key: Clave del valor a obtener

        Returns:
            El valor si existe, None si no existe
        """
        with self._lock:
            if key not in self.cache:
                self._misses += 1
                return None

            # Mover al final (más reciente)
            self.cache.move_to_end(key)
            self._hits += 1
            return self.cache[key]

    def set(self, key: str, value: Any) -> None:
        """
        Guarda un valor en el cache.
        Thread-safe.

        Si el cache está lleno, elimina la entrada menos recientemente usada.

        Args:
            key: Clave del valor
            value: Valor a guardar
        """
        with self._lock:
            if key in self.cache:
                # Ya existe, moverlo al final
                self.cache.move_to_end(key)
            else:
                # Nuevo, verificar capacidad
                if len(self.cache) >= self.max_size:
                    # Eliminar el primero (menos reciente)
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
                    # FIX Cortez36: Use lazy logging formatting
                    logger.debug("LRU cache evicted oldest entry: %s...", oldest_key[:16])

            self.cache[key] = value

    def clear(self) -> None:
        """Limpia todo el cache. Thread-safe."""
        with self._lock:
            self.cache.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del cache. Thread-safe.

        Returns:
            Diccionario con estadísticas (hits, misses, size, hit_rate)
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0

            return {
            "hits": self._hits,
            "misses": self._misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "current_size": len(self.cache),
            "max_size": self.max_size
        }


class LLMResponseCache:
    """
    Cache de respuestas de LLM con TTL (Time To Live).

    Características:
    - Hash de prompt + context como clave
    - TTL configurable (default: 1 hora)
    - LRU eviction cuando se alcanza capacidad máxima
    - Estadísticas de hit/miss rate
    - Thread-safe (para uso con uvicorn workers)
    """

    def __init__(
        self,
        ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        max_entries: int = DEFAULT_CACHE_MAX_SIZE,
        enabled: bool = True
    ):
        """
        Inicializa el cache de respuestas LLM.

        Args:
            ttl_seconds: Tiempo de vida de las entradas en segundos
            max_entries: Número máximo de entradas en cache
            enabled: Si el cache está habilitado
        """
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self.enabled = enabled

        # Cache LRU para las respuestas (ya es thread-safe internamente)
        self._cache = LRUCache(max_size=max_entries)

        # Timestamps para TTL
        self._timestamps: Dict[str, float] = {}
        self._timestamps_lock = threading.Lock()  # Thread-safety para timestamps

        logger.info(
            f"LLM Response Cache initialized: "
            f"enabled={enabled}, ttl={ttl_seconds}s, max_entries={max_entries}"
        )

    def _generate_cache_key(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Genera una clave única para el cache basada en prompt + context + mode + session + salt.

        SECURITY FIX (2025-11-25): Agregado salt institucional y session_id para prevenir:
        - Cache poisoning attacks (attacker no puede pre-generar cache keys)
        - Cross-student cache leakage (cada sesión tiene cache aislado)
        - Timing attacks (keys impredecibles sin salt)

        Args:
            prompt: Prompt del usuario
            context: Contexto adicional (código, archivos, etc.)
            mode: Modo del agente (TUTOR, EVALUATOR, etc.)
            session_id: ID de la sesión (para aislar cache por estudiante)

        Returns:
            Hash SHA256 hexadecimal con salt
        """
        import os

        # Obtener salt desde variable de entorno
        # CRITICAL: Este salt DEBE ser único por institución
        cache_salt = os.getenv("CACHE_SALT", "")

        # Validar que en producción se use un salt personalizado
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production" and not cache_salt:
            logger.warning(
                "SECURITY WARNING: CACHE_SALT not set in production. "
                "Using default salt is insecure. Generate one with: "
                "python -c 'import secrets; print(secrets.token_hex(32))'"
            )
            cache_salt = "default_insecure_salt_CHANGE_IN_PRODUCTION"

        # Serializar datos de entrada de forma determinística
        data = {
            "prompt": prompt,
            "context": context or {},
            "mode": mode or "TUTOR",
            "session_id": session_id or "",  # ✅ Aísla cache por sesión
            "salt": cache_salt,  # ✅ Hace keys impredecibles
            "cache_version": "v2",  # ✅ Permite invalidar cache globalmente
        }

        # JSON con keys ordenadas para consistencia
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=True)

        # Hash SHA256 con salt
        hash_obj = hashlib.sha256(json_str.encode('utf-8'))
        cache_key = hash_obj.hexdigest()

        return cache_key

    def get(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None
    ) -> Optional[str]:
        """
        Obtiene una respuesta del cache si existe y no ha expirado.

        Args:
            prompt: Prompt del usuario
            context: Contexto adicional
            mode: Modo del agente

        Returns:
            La respuesta cacheada si existe y es válida, None en caso contrario
        """
        if not self.enabled:
            return None

        cache_key = self._generate_cache_key(prompt, context, mode)

        # Verificar si existe en cache
        cached_response = self._cache.get(cache_key)

        if cached_response is None:
            # FIX Cortez36: Use lazy logging formatting
            logger.debug("Cache MISS for key: %s...", cache_key[:16])
            # ✅ HIGH-01: Record cache miss metric
            metrics = _get_metrics()
            if metrics:
                metrics.record_cache_operation("llm", hit=False)
            return None

        # Verificar TTL (thread-safe)
        with self._timestamps_lock:
            timestamp = self._timestamps.get(cache_key, 0)
            age_seconds = time.time() - timestamp

            if age_seconds > self.ttl_seconds:
                # Expirado, eliminar
                logger.debug(
                    f"Cache entry EXPIRED (age: {int(age_seconds)}s > TTL: {self.ttl_seconds}s)"
                )
                del self._timestamps[cache_key]
                # ✅ HIGH-01: Record cache miss metric (expired entry)
                metrics = _get_metrics()
                if metrics:
                    metrics.record_cache_operation("llm", hit=False)
                return None

        logger.info(
            f"Cache HIT for prompt: {_sanitize_for_logs(prompt)} "
            f"(age: {int(age_seconds)}s, saved LLM call)"
        )

        # ✅ HIGH-01: Record cache hit metric
        metrics = _get_metrics()
        if metrics:
            metrics.record_cache_operation("llm", hit=True)

        return cached_response

    def set(
        self,
        prompt: str,
        response: str,
        context: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None
    ) -> None:
        """
        Guarda una respuesta en el cache.

        Args:
            prompt: Prompt del usuario
            response: Respuesta del LLM
            context: Contexto adicional
            mode: Modo del agente
        """
        if not self.enabled:
            return

        cache_key = self._generate_cache_key(prompt, context, mode)

        # Guardar respuesta y timestamp (thread-safe)
        self._cache.set(cache_key, response)  # LRUCache.set() ya es thread-safe
        with self._timestamps_lock:
            self._timestamps[cache_key] = time.time()

        logger.debug(
            f"Cache SET for key: {cache_key[:16]}... "
            f"(response length: {len(response)} chars)"
        )

    def clear(self) -> None:
        """Limpia todo el cache. Thread-safe."""
        self._cache.clear()  # LRUCache.clear() ya es thread-safe
        with self._timestamps_lock:
            self._timestamps.clear()
        logger.info("LLM Response Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del cache.

        Returns:
            Diccionario con estadísticas completas
        """
        lru_stats = self._cache.get_stats()

        # Calcular entradas expiradas
        now = time.time()
        expired_count = sum(
            1 for ts in self._timestamps.values()
            if (now - ts) > self.ttl_seconds
        )

        return {
            **lru_stats,
            "enabled": self.enabled,
            "ttl_seconds": self.ttl_seconds,
            "expired_entries": expired_count,
            "active_entries": len(self._timestamps) - expired_count
        }

    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas del cache. Thread-safe.

        Returns:
            Número de entradas eliminadas
        """
        if not self.enabled:
            return 0

        with self._timestamps_lock:
            now = time.time()
            expired_keys = [
                key for key, ts in self._timestamps.items()
                if (now - ts) > self.ttl_seconds
            ]

            for key in expired_keys:
                del self._timestamps[key]
                # El LRU cache se limpiará naturalmente

        if expired_keys:
            # FIX Cortez36: Use lazy logging formatting
            logger.info("Cleaned up %d expired cache entries", len(expired_keys))

        return len(expired_keys)


# Instancia global del cache (singleton)
# En producción con múltiples workers, usar Redis
_global_cache: Optional[LLMResponseCache] = None
_cache_lock = threading.Lock()  # Lock para thread-safety en singleton


def get_llm_cache(
    ttl_seconds: int = 3600,
    max_entries: int = 1000,
    enabled: bool = True
) -> LLMResponseCache:
    """
    Obtiene la instancia global del cache LLM (singleton).

    Thread-safe usando double-checked locking pattern para prevenir race conditions
    en ambientes multi-threaded (ej: uvicorn con múltiples workers).

    Args:
        ttl_seconds: TTL para nuevas instancias
        max_entries: Máximo de entradas para nuevas instancias
        enabled: Si el cache está habilitado

    Returns:
        Instancia del cache
    """
    global _global_cache

    # First check (without lock, fast path)
    if _global_cache is None:
        # Second check (with lock, ensures only one thread initializes)
        with _cache_lock:
            if _global_cache is None:
                _global_cache = LLMResponseCache(
                    ttl_seconds=ttl_seconds,
                    max_entries=max_entries,
                    enabled=enabled
                )

    return _global_cache


# BE-MEM-002: Scheduled cache cleanup task
_cleanup_task: Optional["asyncio.Task"] = None
_cleanup_running = False


async def start_periodic_cache_cleanup(interval_seconds: Optional[int] = None) -> None:
    """
    BE-MEM-002: Start periodic cache cleanup background task.

    This prevents unbounded memory growth by periodically removing
    expired cache entries.

    Args:
        interval_seconds: Cleanup interval (default: CACHE_CLEANUP_INTERVAL_SECONDS)
    """
    import asyncio
    global _cleanup_task, _cleanup_running

    if _cleanup_running:
        logger.warning("Cache cleanup task already running")
        return

    interval = interval_seconds or CACHE_CLEANUP_INTERVAL_SECONDS
    _cleanup_running = True

    async def cleanup_loop():
        global _cleanup_running
        try:
            logger.info(
                "BE-MEM-002: Starting periodic cache cleanup (interval: %ds)",
                interval
            )
            while _cleanup_running:
                await asyncio.sleep(interval)
                if _global_cache:
                    expired_count = _global_cache.cleanup_expired()
                    if expired_count > 0:
                        logger.debug(
                            "Periodic cleanup removed %d expired entries", expired_count
                        )
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
        except Exception as e:
            logger.error("Error in cache cleanup task: %s", e, exc_info=True)
        finally:
            _cleanup_running = False

    _cleanup_task = asyncio.create_task(cleanup_loop())
    # Add done callback for error logging
    _cleanup_task.add_done_callback(_log_task_errors)


def _log_task_errors(task: "asyncio.Task") -> None:
    """Log any unhandled exceptions from background tasks."""
    try:
        exc = task.exception()
        if exc:
            logger.error("Background cache cleanup task failed: %s", exc, exc_info=exc)
    except asyncio.CancelledError:
        pass


async def stop_periodic_cache_cleanup() -> None:
    """Stop the periodic cache cleanup task."""
    global _cleanup_task, _cleanup_running

    _cleanup_running = False
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        try:
            import asyncio
            await asyncio.wait_for(_cleanup_task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        _cleanup_task = None
        logger.info("Cache cleanup task stopped")