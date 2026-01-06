"""
Embedding Provider - Generacion de embeddings vectoriales via Ollama.

Cortez87: Implementacion de RAG para enriquecer respuestas de agentes.
FIX Cortez88 HIGH-RESOURCE-001: Added async context manager for proper resource cleanup

Este modulo proporciona la transformacion de texto a representaciones
vectoriales de 384 dimensiones usando nomic-embed-text via Ollama.

Caracteristicas:
- Costo: $0 (self-hosted via Ollama)
- Dimensiones: 384 (nomic-embed-text)
- Latencia: 10-50ms por documento
- Cache integrado via Redis para consultas repetidas
- Fallback a embeddings mock para tests
"""
import hashlib
import logging
import os
import asyncio
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)

# Dimension de embeddings (nomic-embed-text = 384)
EMBEDDING_DIMENSIONS = 384


class EmbeddingProvider(ABC):
    """Interfaz abstracta para proveedores de embeddings."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Genera embeddings para multiples textos."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Cierra conexiones y libera recursos."""
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Proveedor de embeddings usando Ollama + nomic-embed-text.

    Transforma texto en representaciones vectoriales de 384 dimensiones
    que capturan el significado semantico del contenido.

    La vectorizacion se realiza localmente a traves de Ollama,
    eliminando costos de API externos y garantizando privacidad
    de los datos (ningun contenido sale del servidor).

    Attributes:
        base_url: URL del servidor Ollama
        model: Modelo de embeddings (default: nomic-embed-text)
        timeout: Timeout para requests HTTP
        cache: Cache Redis opcional para evitar re-computacion
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "nomic-embed-text",
        timeout: float = 30.0,
        cache: Optional[Any] = None  # LLMResponseCache or similar
    ):
        """
        Inicializa el proveedor de embeddings.

        Args:
            base_url: URL de Ollama (default: env OLLAMA_EMBEDDINGS_URL o localhost)
            model: Modelo de embeddings
            timeout: Timeout en segundos
            cache: Cache opcional para embeddings
        """
        self.base_url = base_url or os.getenv(
            "OLLAMA_EMBEDDINGS_URL",
            os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        )
        self.model = model
        self.timeout = timeout
        self.cache = cache
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(
            f"OllamaEmbeddingProvider initialized: "
            f"url={self.base_url}, model={self.model}"
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP asincrono."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout)
            )
        return self._client

    def _cache_key(self, text: str) -> str:
        """
        Genera una clave de cache unica para un texto.

        Usa MD5 para producir una clave de longitud fija
        independientemente del tamano del texto de entrada.
        """
        return f"emb:v1:{hashlib.md5(text.encode()).hexdigest()}"

    async def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Intenta obtener embedding del cache."""
        if not self.cache:
            return None

        cache_key = self._cache_key(text)
        try:
            # El cache puede ser sync o async
            if hasattr(self.cache, 'get'):
                cached = self.cache.get(cache_key)
                if asyncio.iscoroutine(cached):
                    cached = await cached
                return cached
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
        return None

    async def _set_to_cache(self, text: str, embedding: List[float]) -> None:
        """Guarda embedding en cache."""
        if not self.cache:
            return

        cache_key = self._cache_key(text)
        try:
            if hasattr(self.cache, 'set'):
                result = self.cache.set(cache_key, embedding)
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")

    async def embed(self, text: str) -> List[float]:
        """
        Genera el embedding vectorial para un texto.

        El proceso:
        1. Verifica si existe en cache
        2. Si no, invoca a Ollama
        3. Almacena resultado en cache
        4. Retorna vector de 384 dimensiones

        Args:
            text: Texto a vectorizar (max recomendado: 2000 caracteres)

        Returns:
            Lista de 384 numeros flotantes representando el embedding

        Raises:
            httpx.HTTPError: Si falla la conexion con Ollama
            ValueError: Si la respuesta es invalida
        """
        # Verificar cache primero
        cached = await self._get_from_cache(text)
        if cached is not None:
            logger.debug(f"Embedding cache HIT for text length {len(text)}")
            return cached

        # Generar embedding via Ollama
        client = await self._get_client()

        try:
            response = await client.post(
                "/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()

            embedding = data.get("embedding")
            if not embedding:
                raise ValueError(f"No embedding in response: {data}")

            # Validar dimensiones
            if len(embedding) != EMBEDDING_DIMENSIONS:
                logger.warning(
                    f"Unexpected embedding dimensions: {len(embedding)} "
                    f"(expected {EMBEDDING_DIMENSIONS})"
                )

            # Guardar en cache
            await self._set_to_cache(text, embedding)

            logger.debug(
                f"Generated embedding for text length {len(text)}, "
                f"dimensions: {len(embedding)}"
            )
            return embedding

        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            raise

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Genera embeddings para multiples textos en lotes.

        Para evitar sobrecargar Ollama, procesa los textos en
        lotes de tamano configurable con concurrencia limitada.

        Args:
            texts: Lista de textos a vectorizar
            batch_size: Cantidad de textos a procesar simultaneamente

        Returns:
            Lista de embeddings en el mismo orden que los textos de entrada
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Procesar batch concurrentemente
            batch_embeddings = await asyncio.gather(
                *[self.embed(text) for text in batch],
                return_exceptions=True
            )

            # Manejar errores individuales
            for j, result in enumerate(batch_embeddings):
                if isinstance(result, Exception):
                    logger.error(f"Failed to embed text {i + j}: {result}")
                    # Usar embedding vacio como fallback
                    embeddings.append([0.0] * EMBEDDING_DIMENSIONS)
                else:
                    embeddings.append(result)

            # Breve pausa entre batches para no saturar
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return embeddings

    async def close(self) -> None:
        """Cierra el cliente HTTP liberando recursos."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.debug("OllamaEmbeddingProvider client closed")

    # FIX Cortez88 HIGH-RESOURCE-001: Add async context manager support
    async def __aenter__(self) -> "OllamaEmbeddingProvider":
        """Context manager entry - initialize client."""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - cleanup resources."""
        await self.close()


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Proveedor de embeddings mock para tests y desarrollo.

    Genera embeddings deterministicos basados en hash del texto,
    permitiendo tests sin dependencia de Ollama.
    """

    def __init__(self, dimensions: int = EMBEDDING_DIMENSIONS):
        self.dimensions = dimensions
        logger.info(f"MockEmbeddingProvider initialized (dimensions={dimensions})")

    async def embed(self, text: str) -> List[float]:
        """Genera embedding deterministico basado en hash."""
        # Usar hash para generar valores consistentes
        text_hash = hashlib.sha256(text.encode()).digest()

        # Convertir bytes a floats normalizados [-1, 1]
        embedding = []
        for i in range(self.dimensions):
            byte_val = text_hash[i % len(text_hash)]
            normalized = (byte_val / 127.5) - 1.0  # Normalizar a [-1, 1]
            embedding.append(normalized)

        return embedding

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """Genera embeddings para multiples textos."""
        return [await self.embed(text) for text in texts]

    async def close(self) -> None:
        """No-op para mock."""
        pass


def get_embedding_provider(
    provider_type: Optional[str] = None,
    **kwargs
) -> EmbeddingProvider:
    """
    Factory para obtener el proveedor de embeddings apropiado.

    Args:
        provider_type: Tipo de proveedor ('ollama', 'mock', None=auto)
        **kwargs: Argumentos adicionales para el proveedor

    Returns:
        Instancia de EmbeddingProvider
    """
    # Auto-detect based on environment
    if provider_type is None:
        rag_enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"
        if not rag_enabled:
            logger.info("RAG disabled, using MockEmbeddingProvider")
            return MockEmbeddingProvider(**kwargs)

        # Check if Ollama is configured
        ollama_url = os.getenv("OLLAMA_EMBEDDINGS_URL", os.getenv("OLLAMA_BASE_URL"))
        if ollama_url:
            provider_type = "ollama"
        else:
            logger.warning("No OLLAMA_EMBEDDINGS_URL configured, using mock")
            provider_type = "mock"

    if provider_type == "ollama":
        return OllamaEmbeddingProvider(**kwargs)
    elif provider_type == "mock":
        return MockEmbeddingProvider(**kwargs)
    else:
        raise ValueError(f"Unknown embedding provider type: {provider_type}")


__all__ = [
    "EmbeddingProvider",
    "OllamaEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
    "EMBEDDING_DIMENSIONS",
]
