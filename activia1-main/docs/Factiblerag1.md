# Guía de Implementación RAG: Integración Segura y Progresiva

**Autor**: Claude Code (Arquitectura de Software)
**Fecha**: 3 de enero de 2026
**Versión**: 1.0
**Prerrequisito**: Lectura previa de `factiblerag.md`
**Estado del Proyecto**: Post-Cortez71 (71 auditorías, 6 agentes IA, trazabilidad N4)

---

## Introducción

Este documento presenta una guía exhaustiva para implementar las capacidades de Retrieval-Augmented Generation propuestas en `rag1.txt` de manera que fortalezca el sistema existente sin introducir regresiones ni romper la arquitectura madura que se ha construido a lo largo de más de setenta auditorías de calidad. La premisa fundamental que guía esta implementación es que el sistema AI-Native MVP ya posee una arquitectura robusta con seis agentes de inteligencia artificial especializados, un sistema de trazabilidad cognitiva de cuatro niveles, y una infraestructura de evaluación de procesos única en su tipo. Por lo tanto, cualquier adición debe complementar estas capacidades, nunca reemplazarlas.

El enfoque arquitectónico que se propone sigue el principio de "capas aditivas": cada nuevo componente se añade como una capa opcional que enriquece las capacidades existentes pero que puede desactivarse sin afectar el funcionamiento base del sistema. Este diseño permite un despliegue gradual, pruebas exhaustivas en cada fase, y la posibilidad de revertir cambios si se detectan problemas inesperados.

---

## Parte I: Fundamentos Arquitectónicos

### Capítulo 1: Anatomía del Sistema Actual

Antes de introducir cualquier cambio, es imperativo comprender profundamente cómo funciona el sistema actual. El AI-Native MVP está construido sobre una arquitectura de capas bien definidas donde cada componente tiene responsabilidades claras y límites establecidos.

#### 1.1 La Capa de Persistencia

El sistema utiliza PostgreSQL como base de datos principal con SQLAlchemy como ORM. Los modelos están organizados en catorce archivos modulares dentro de `backend/database/models/`, resultado de la refactorización Cortez42 que descompuso un archivo monolítico de más de mil setecientas líneas. Esta modularización no fue cosmética: cada modelo representa un agregado del dominio con sus propias reglas de negocio y validaciones.

El modelo `SessionDB` representa el concepto central de sesión de aprendizaje. Cada sesión pertenece a un estudiante, está asociada a una actividad, y mantiene el estado cognitivo actual del estudiante. Las sesiones no almacenan las interacciones directamente; en su lugar, las interacciones generan trazas cognitivas que se persisten en `CognitiveTraceDB`. Esta separación es crucial porque permite que el sistema analice patrones de comportamiento sin sobrecargar el modelo de sesión.

El modelo `ActivityDB` representa el trabajo académico que el docente diseña. Contiene las instrucciones, los criterios de evaluación, y un campo JSON llamado `policies` que encapsula las reglas pedagógicas: cuántas pistas se permiten, qué penalizaciones aplican, cuál es el nivel de ayuda máximo que el tutor puede ofrecer. Esta flexibilidad mediante configuración JSON es un patrón que debemos preservar al añadir capacidades RAG.

El modelo `ExerciseDB` y sus relacionados (`ExerciseHintDB`, `ExerciseTestDB`, `ExerciseAttemptDB`) forman el subsistema de entrenamiento digital. Los ejercicios tienen campos como `mission_markdown` para la descripción, `starter_code` para el código inicial, y `solution_code` para la solución de referencia. Las pistas están ordenadas y tienen un costo asociado. Los tests definen las pruebas automatizadas que validan el código del estudiante.

#### 1.2 La Capa de Repositorios

Los repositorios encapsulan todas las operaciones de persistencia siguiendo el patrón Repository. Hay trece repositorios especializados, cada uno responsable de un agregado del dominio. El `BaseRepository` define convenciones de nomenclatura documentadas en Cortez66: métodos como `get_by_id()`, `get_by_*()` para búsquedas específicas, y `get_by_*_ids()` para operaciones en lote que previenen el problema N+1.

Un patrón importante que debe preservarse es el de carga eager mediante `selectinload()`. Cuando se recupera una sesión con `load_relations=True`, el repositorio carga en una sola consulta las trazas, riesgos y evaluaciones asociadas. Este patrón evita múltiples roundtrips a la base de datos y es crítico para el rendimiento del sistema.

#### 1.3 La Capa de Agentes

El corazón inteligente del sistema reside en seis agentes de IA, cada uno especializado en una tarea pedagógica específica. El agente T-IA-Cog (Tutor Cognitivo) implementa el patrón Strategy con cinco modos pedagógicos: socrático, explicativo, guiado, metacognitivo, y de pistas para entrenamiento. Cada estrategia genera respuestas apropiadas para el estado cognitivo del estudiante.

El agente E-IA-Proc (Evaluador de Procesos) analiza no el producto final sino el proceso de resolución. Examina las trazas cognitivas para determinar si el estudiante está desarrollando autonomía o si está delegando excesivamente en la IA.

El agente AR-IA (Analista de Riesgos) implementa un modelo de cinco dimensiones: cognitiva, ética, epistémica, técnica y de gobernanza. Utiliza optimizaciones algorítmicas como bisect para búsquedas O(n log n) y fingerprinting para detección de duplicados en O(n).

El agente GOV-IA (Gobernanza) implementa un sistema de semáforos que controla el nivel de autonomía que el sistema permite al estudiante. Un semáforo verde indica que el estudiante puede recibir ayuda completa; uno amarillo sugiere que debe esforzarse más antes de pedir ayuda; uno rojo indica que el estudiante está delegando demasiado y debe trabajar de forma independiente.

#### 1.4 El Gateway de IA

El `AIGateway` es el orquestador central y su característica más importante es que es stateless. No mantiene estado en memoria; toda la información persiste en PostgreSQL a través de los repositorios. Este diseño permite escalar horizontalmente desplegando múltiples instancias del gateway detrás de un balanceador de carga.

El gateway coordina el flujo de una interacción típica: primero el motor cognitivo (CRPE) clasifica el prompt del estudiante detectando hasta ciento treinta y siete señales diferentes; luego el factory de modos selecciona la estrategia apropiada; el agente tutor genera la respuesta; el coordinador de trazas persiste la interacción; y el coordinador de riesgos analiza si hay patrones preocupantes.

Los coordinadores (`TraceCoordinator`, `RiskCoordinator`, `ResponseGenerators`) fueron extraídos del gateway monolítico en Cortez66 para mejorar la cohesión y facilitar el testing. Cada coordinador tiene una responsabilidad única y bien definida.

---

## Parte II: Estrategia de Integración RAG

### Capítulo 2: El Principio de No Regresión

La regla cardinal de esta implementación es que ningún cambio debe romper funcionalidad existente. Esto se logra mediante tres mecanismos: feature flags, interfaces de abstracción, y tests de regresión automatizados.

#### 2.1 Sistema de Feature Flags

Cada nueva capacidad RAG se introduce detrás de un feature flag. En el backend, estos flags se definen en `backend/api/config.py`:

```python
# RAG Integration Feature Flags (Phase 1+)
RAG_ENABLED: bool = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_RETRIEVAL_TOP_K: int = int(os.getenv("RAG_RETRIEVAL_TOP_K", "6"))
RAG_EMBEDDING_MODEL: str = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
RAG_SIMILARITY_THRESHOLD: float = float(os.getenv("RAG_SIMILARITY_THRESHOLD", "0.7"))
```

En el frontend, los flags se centralizan en `frontEnd/src/shared/config/featureFlags.config.ts`:

```typescript
export const featureFlags = {
  // ... flags existentes
  enableRAGIntegration: parseBoolEnv(
    import.meta.env.VITE_FEATURE_RAG_INTEGRATION,
    false
  ),
  enableRAGSourceDisplay: parseBoolEnv(
    import.meta.env.VITE_FEATURE_RAG_SOURCES,
    false
  ),
};
```

Cuando `RAG_ENABLED=false`, el sistema funciona exactamente como antes. Ningún código RAG se ejecuta, ninguna tabla RAG se consulta, ningún embedding se genera. Esto permite desplegar el código a producción antes de activar la funcionalidad, reduciendo el riesgo de regresiones.

#### 2.2 Interfaces de Abstracción

Los nuevos componentes RAG se diseñan contra interfaces abstractas, no contra implementaciones concretas. Esto permite cambiar la implementación sin afectar el código que la consume.

```python
from abc import ABC, abstractmethod
from typing import List, Protocol

class EmbeddingProvider(Protocol):
    """Protocolo para proveedores de embeddings."""

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos."""
        ...

    @property
    def dimension(self) -> int:
        """Dimensión de los vectores generados."""
        ...

class RAGRetriever(ABC):
    """Interfaz abstracta para retrieval de documentos."""

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        unidad_id: int,
        top_k: int = 6,
        threshold: float = 0.7
    ) -> List[RetrievedChunk]:
        """Recupera los chunks más relevantes para una consulta."""
        pass
```

Con estas interfaces, podemos comenzar con una implementación simple usando nomic-embed-text vía Ollama, y luego migrar a OpenAI embeddings o a un servicio dedicado sin cambiar el código del gateway.

#### 2.3 Tests de Regresión

Antes de cada fase de implementación, se ejecuta la suite completa de tests:

```bash
# Backend: cobertura mínima 70%
pytest tests/ -v --cov=backend --cov-fail-under=70

# Frontend: linting + type-check + tests
npm run lint && npm run type-check && npm test
```

Además, se añaden tests específicos para verificar que las rutas existentes funcionan con `RAG_ENABLED=false`:

```python
@pytest.mark.parametrize("rag_enabled", [False, True])
async def test_tutor_interaction_with_rag_flag(
    client: TestClient,
    rag_enabled: bool,
    monkeypatch
):
    """Verifica que la interacción tutor funciona independientemente del flag RAG."""
    monkeypatch.setenv("RAG_ENABLED", str(rag_enabled).lower())

    response = await client.post("/api/v1/sessions/", json={...})
    assert response.status_code == 201

    response = await client.post("/api/v1/interactions/", json={...})
    assert response.status_code == 200
    assert "response" in response.json()
```

---

### Capítulo 3: Fase 1 — Infraestructura pgvector

La primera fase establece la infraestructura de almacenamiento vectorial sin afectar ningún flujo existente. Es puramente aditiva: nuevas tablas, nuevos servicios, nuevos endpoints, todos opcionales.

#### 3.1 Preparación de PostgreSQL

El primer paso es habilitar la extensión pgvector en PostgreSQL. Esto requiere que el servidor PostgreSQL tenga la extensión instalada (disponible en la imagen Docker `pgvector/pgvector:pg16`).

```sql
-- Archivo: backend/database/migrations/add_pgvector_support.py
-- Esta migración es idempotente y segura de ejecutar múltiples veces

CREATE EXTENSION IF NOT EXISTS vector;

-- Verificación: esta consulta debe retornar 'vector'
SELECT typname FROM pg_type WHERE typname = 'vector';
```

La migración se ejecuta con el comando existente:

```bash
python -m backend.database.migrations.add_pgvector_support
```

#### 3.2 Modelo de Chunks

Se crea un nuevo archivo de modelo `backend/database/models/rag.py` siguiendo las convenciones establecidas:

```python
"""
RAG Models - Modelos para Retrieval-Augmented Generation

Este módulo es ADITIVO: no modifica ningún modelo existente.
Todos los modelos aquí son opcionales y solo se usan cuando RAG_ENABLED=true.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, BigInteger, Integer, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
import uuid

from .base import Base, BaseModel

# Dimensión del embedding (nomic-embed-text = 384, OpenAI = 1536)
# Configurable via variable de entorno para flexibilidad futura
import os
EMBEDDING_DIM = int(os.getenv("RAG_EMBEDDING_DIM", "384"))


class UnidadDocumentoDB(BaseModel):
    """
    Documento asociado a una unidad académica.

    Representa un PDF (enunciado o material de apoyo) que el docente
    sube para una unidad específica. El contenido se procesa y almacena
    como chunks con embeddings.
    """
    __tablename__ = "unidad_documento"
    __table_args__ = (
        Index("idx_unidad_doc_unidad", "unidad_id"),
        Index("idx_unidad_doc_tipo_estado", "tipo", "estado"),
        CheckConstraint(
            "tipo IN ('ENUNCIADO', 'MATERIAL')",
            name="ck_unidad_doc_tipo"
        ),
        CheckConstraint(
            "estado IN ('BORRADOR', 'PUBLICADO', 'ARCHIVADO')",
            name="ck_unidad_doc_estado"
        ),
    )

    unidad_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False, default="MATERIAL")
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False, default="application/pdf")
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estado: Mapped[str] = mapped_column(Text, nullable=False, default="BORRADOR")
    created_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    ingestas = relationship("DocumentoIngestaDB", back_populates="documento")
    chunks = relationship("DocumentoChunkDB", back_populates="documento")


class DocumentoIngestaDB(BaseModel):
    """
    Registro de procesamiento de un documento.

    Cada vez que un documento se procesa (inicial o re-ingesta),
    se crea un registro de ingesta con su versión y estado.
    Esto permite auditoría completa y rollback si es necesario.
    """
    __tablename__ = "documento_ingesta"
    __table_args__ = (
        UniqueConstraint("unidad_documento_id", "version", name="uq_ingesta_doc_version"),
        Index("idx_ingesta_doc_status", "unidad_documento_id", "status"),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'OK', 'ERROR')",
            name="ck_ingesta_status"
        ),
    )

    unidad_documento_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("unidad_documento.id", ondelete="CASCADE"),
        nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    parser: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    text_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_msg: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relaciones
    documento = relationship("UnidadDocumentoDB", back_populates="ingestas")
    chunks = relationship("DocumentoChunkDB", back_populates="ingesta")


class DocumentoChunkDB(Base):
    """
    Fragmento de texto con embedding vectorial.

    Representa un chunk de ~1200 caracteres extraído de un documento PDF.
    Incluye el embedding para búsqueda por similitud y metadatos
    para trazabilidad (páginas de origen, documento fuente).

    NOTA: No hereda de BaseModel porque usa BigInteger como PK
    en lugar de UUID, optimizando para volumen de datos.
    """
    __tablename__ = "documento_chunk"
    __table_args__ = (
        UniqueConstraint("ingesta_id", "chunk_index", name="uq_chunk_ingesta_idx"),
        Index("idx_chunk_unidad", "unidad_id"),
        Index("idx_chunk_doc", "unidad_documento_id"),
        # El índice HNSW se crea en la migración con SQL raw
        # porque SQLAlchemy no lo soporta nativamente
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    unidad_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    unidad_documento_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("unidad_documento.id", ondelete="CASCADE"),
        nullable=False
    )
    ingesta_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documento_ingesta.id", ondelete="CASCADE"),
        nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    token_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    metadata: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )

    # Relaciones
    documento = relationship("UnidadDocumentoDB", back_populates="chunks")
    ingesta = relationship("DocumentoIngestaDB", back_populates="chunks")
```

#### 3.3 Repositorio RAG

El repositorio sigue las convenciones de nomenclatura establecidas en Cortez66:

```python
"""
RAG Repository - Operaciones de persistencia para el sistema RAG

Sigue las convenciones de BaseRepository:
- get_by_id(): Búsqueda por ID
- get_by_*(): Búsquedas por campos específicos
- get_similar(): Búsqueda vectorial (nueva operación específica de RAG)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.rag import DocumentoChunkDB, UnidadDocumentoDB, DocumentoIngestaDB


class RAGRepository(BaseRepository):
    """Repositorio para operaciones RAG con pgvector."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ==================== Documento ====================

    def create_documento(
        self,
        unidad_id: int,
        tipo: str,
        titulo: str,
        storage_key: str,
        sha256: str,
        size_bytes: int,
        created_by: Optional[str] = None
    ) -> UnidadDocumentoDB:
        """Crea un nuevo documento para una unidad."""
        doc = UnidadDocumentoDB(
            unidad_id=unidad_id,
            tipo=tipo,
            titulo=titulo,
            storage_key=storage_key,
            sha256=sha256,
            size_bytes=size_bytes,
            created_by=created_by
        )
        self.db.add(doc)
        self.db.flush()
        return doc

    def get_documento_by_id(self, doc_id: int) -> Optional[UnidadDocumentoDB]:
        """Obtiene un documento por su ID."""
        return self.db.get(UnidadDocumentoDB, doc_id)

    def get_documentos_by_unidad(
        self,
        unidad_id: int,
        solo_publicados: bool = True
    ) -> List[UnidadDocumentoDB]:
        """Obtiene todos los documentos de una unidad."""
        stmt = select(UnidadDocumentoDB).where(
            UnidadDocumentoDB.unidad_id == unidad_id
        )
        if solo_publicados:
            stmt = stmt.where(UnidadDocumentoDB.estado == "PUBLICADO")
        stmt = stmt.order_by(UnidadDocumentoDB.orden.asc())
        return list(self.db.execute(stmt).scalars().all())

    # ==================== Ingesta ====================

    def create_ingesta(
        self,
        unidad_documento_id: int,
        parser: str = "pymupdf"
    ) -> DocumentoIngestaDB:
        """Crea un registro de ingesta para un documento."""
        # Determinar siguiente versión
        max_version = self.db.execute(
            select(func.max(DocumentoIngestaDB.version))
            .where(DocumentoIngestaDB.unidad_documento_id == unidad_documento_id)
        ).scalar_one_or_none() or 0

        ingesta = DocumentoIngestaDB(
            unidad_documento_id=unidad_documento_id,
            version=max_version + 1,
            status="PENDING",
            parser=parser
        )
        self.db.add(ingesta)
        self.db.flush()
        return ingesta

    def update_ingesta_status(
        self,
        ingesta_id,
        status: str,
        **kwargs
    ) -> None:
        """Actualiza el estado de una ingesta."""
        ingesta = self.db.get(DocumentoIngestaDB, ingesta_id)
        if ingesta:
            ingesta.status = status
            for key, value in kwargs.items():
                if hasattr(ingesta, key):
                    setattr(ingesta, key, value)
            self.db.flush()

    # ==================== Chunks ====================

    def create_chunks_batch(
        self,
        chunks_data: List[Dict[str, Any]]
    ) -> int:
        """Crea múltiples chunks en una sola operación."""
        chunks = [DocumentoChunkDB(**data) for data in chunks_data]
        self.db.add_all(chunks)
        self.db.flush()
        return len(chunks)

    def get_similar_chunks(
        self,
        embedding: List[float],
        unidad_id: int,
        top_k: int = 6,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda por similitud vectorial usando cosine distance.

        Retorna los chunks más similares al embedding de consulta,
        filtrados por unidad_id y ordenados por distancia.
        """
        # Usar la función de distancia coseno de pgvector
        distance = DocumentoChunkDB.embedding.cosine_distance(embedding)

        stmt = (
            select(
                DocumentoChunkDB.id,
                DocumentoChunkDB.content_text,
                DocumentoChunkDB.page_from,
                DocumentoChunkDB.page_to,
                DocumentoChunkDB.unidad_documento_id,
                DocumentoChunkDB.metadata,
                distance.label("distance")
            )
            .where(DocumentoChunkDB.unidad_id == unidad_id)
            .where(distance < (1 - threshold))  # Convertir threshold a distancia
            .order_by(distance.asc())
            .limit(top_k)
        )

        results = self.db.execute(stmt).mappings().all()
        return [
            {
                "chunk_id": r["id"],
                "text": r["content_text"],
                "page_from": r["page_from"],
                "page_to": r["page_to"],
                "documento_id": r["unidad_documento_id"],
                "metadata": r["metadata"],
                "similarity": 1 - r["distance"]  # Convertir distancia a similitud
            }
            for r in results
        ]

    def delete_chunks_by_ingesta(self, ingesta_id) -> int:
        """Elimina todos los chunks de una ingesta específica."""
        result = self.db.execute(
            DocumentoChunkDB.__table__.delete()
            .where(DocumentoChunkDB.ingesta_id == ingesta_id)
        )
        self.db.flush()
        return result.rowcount
```

#### 3.4 Servicio de Embeddings

El servicio de embeddings se diseña con abstracción para permitir cambiar el proveedor:

```python
"""
Embedding Service - Generación de embeddings vectoriales

Abstrae el proveedor de embeddings para permitir cambios sin modificar
el código consumidor. Soporta Ollama (local) y puede extenderse a OpenAI.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """Interfaz abstracta para proveedores de embeddings."""

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para una lista de textos."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensión de los vectores generados."""
        pass


class OllamaEmbeddingProvider(EmbeddingProvider):
    """
    Proveedor de embeddings usando Ollama local.

    Usa nomic-embed-text por defecto (384 dimensiones).
    Configuración:
    - OLLAMA_BASE_URL: URL del servidor Ollama
    - RAG_EMBEDDING_MODEL: Modelo a usar
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._dimension: Optional[int] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    @property
    def dimension(self) -> int:
        """Dimensión basada en el modelo."""
        if self._dimension is None:
            # Dimensiones conocidas de modelos comunes
            dimensions = {
                "nomic-embed-text": 384,
                "mxbai-embed-large": 1024,
                "all-minilm": 384,
            }
            self._dimension = dimensions.get(self.model, 384)
        return self._dimension

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos.

        Procesa en lotes para evitar timeouts con textos largos.
        """
        client = await self._get_client()
        embeddings = []

        for text in texts:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.model, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                embeddings.append(data["embedding"])
            except Exception as e:
                logger.error(f"Error generando embedding: {e}")
                raise

        return embeddings

    async def close(self):
        """Cierra el cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Factory para crear el proveedor según configuración
def create_embedding_provider() -> EmbeddingProvider:
    """Crea el proveedor de embeddings según configuración."""
    import os

    provider_type = os.getenv("RAG_EMBEDDING_PROVIDER", "ollama")

    if provider_type == "ollama":
        return OllamaEmbeddingProvider(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
        )
    else:
        raise ValueError(f"Proveedor de embeddings no soportado: {provider_type}")
```

#### 3.5 Migración de Base de Datos

La migración se estructura para ser reversible y segura:

```python
"""
Migration: add_rag_infrastructure

Añade las tablas y extensiones necesarias para RAG con pgvector.
Esta migración es ADITIVA y no modifica tablas existentes.

Para ejecutar:
    python -m backend.database.migrations.add_rag_infrastructure

Para revertir:
    python -m backend.database.migrations.add_rag_infrastructure --rollback
"""

import sys
from sqlalchemy import text
from backend.database.config import get_engine

UPGRADE_SQL = """
-- Extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de documentos por unidad
CREATE TABLE IF NOT EXISTS unidad_documento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unidad_id BIGINT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'MATERIAL',
    titulo TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
    orden INTEGER NOT NULL DEFAULT 1,
    estado TEXT NOT NULL DEFAULT 'BORRADOR',
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_unidad_doc_tipo CHECK (tipo IN ('ENUNCIADO', 'MATERIAL')),
    CONSTRAINT ck_unidad_doc_estado CHECK (estado IN ('BORRADOR', 'PUBLICADO', 'ARCHIVADO'))
);

CREATE INDEX IF NOT EXISTS idx_unidad_doc_unidad ON unidad_documento(unidad_id);
CREATE INDEX IF NOT EXISTS idx_unidad_doc_tipo_estado ON unidad_documento(tipo, estado);

-- Tabla de ingestas (procesamiento de documentos)
CREATE TABLE IF NOT EXISTS documento_ingesta (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unidad_documento_id UUID NOT NULL REFERENCES unidad_documento(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'PENDING',
    parser TEXT,
    text_hash TEXT,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    error_msg TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_ingesta_doc_version UNIQUE (unidad_documento_id, version),
    CONSTRAINT ck_ingesta_status CHECK (status IN ('PENDING', 'PROCESSING', 'OK', 'ERROR'))
);

CREATE INDEX IF NOT EXISTS idx_ingesta_doc_status ON documento_ingesta(unidad_documento_id, status);

-- Tabla de chunks con embeddings
CREATE TABLE IF NOT EXISTS documento_chunk (
    id BIGSERIAL PRIMARY KEY,
    unidad_id BIGINT NOT NULL,
    unidad_documento_id UUID NOT NULL REFERENCES unidad_documento(id) ON DELETE CASCADE,
    ingesta_id UUID NOT NULL REFERENCES documento_ingesta(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    page_from INTEGER,
    page_to INTEGER,
    token_count INTEGER,
    content_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chunk_ingesta_idx UNIQUE (ingesta_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunk_unidad ON documento_chunk(unidad_id);
CREATE INDEX IF NOT EXISTS idx_chunk_doc ON documento_chunk(unidad_documento_id);

-- Índice HNSW para búsqueda vectorial eficiente
-- Este índice usa cosine distance (vector_cosine_ops)
CREATE INDEX IF NOT EXISTS idx_chunk_embedding_hnsw
ON documento_chunk
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
"""

DOWNGRADE_SQL = """
-- Revertir en orden inverso
DROP INDEX IF EXISTS idx_chunk_embedding_hnsw;
DROP INDEX IF EXISTS idx_chunk_doc;
DROP INDEX IF EXISTS idx_chunk_unidad;
DROP TABLE IF EXISTS documento_chunk;

DROP INDEX IF EXISTS idx_ingesta_doc_status;
DROP TABLE IF EXISTS documento_ingesta;

DROP INDEX IF EXISTS idx_unidad_doc_tipo_estado;
DROP INDEX IF EXISTS idx_unidad_doc_unidad;
DROP TABLE IF EXISTS unidad_documento;

-- NO eliminamos la extensión vector porque podría usarse en otro lugar
-- DROP EXTENSION IF EXISTS vector;
"""


def upgrade():
    """Aplica la migración."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(UPGRADE_SQL))
        conn.commit()
    print("✓ Migración RAG aplicada exitosamente")


def downgrade():
    """Revierte la migración."""
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text(DOWNGRADE_SQL))
        conn.commit()
    print("✓ Migración RAG revertida exitosamente")


if __name__ == "__main__":
    if "--rollback" in sys.argv:
        downgrade()
    else:
        upgrade()
```

---

### Capítulo 4: Fase 2 — Catálogo Académico Extendido

Esta fase añade la jerarquía Materia → Unidad manteniendo compatibilidad total con el modelo actual de Actividades.

#### 4.1 Principio de Extensión No Destructiva

La clave de esta fase es que `ActivityDB` existente NO se modifica de forma destructiva. En lugar de reescribir el modelo, se añade un campo opcional `unidad_id` que permite asociar actividades a unidades cuando el docente así lo desee.

```python
# Añadir a backend/database/models/activity.py
# DESPUÉS de los campos existentes, SIN modificar nada previo

# Campo OPCIONAL para integración con catálogo académico
# Las actividades existentes siguen funcionando sin cambios
unidad_id: Mapped[Optional[int]] = mapped_column(
    BigInteger,
    ForeignKey("unidad.id", ondelete="SET NULL"),
    nullable=True,  # CRÍTICO: nullable=True para compatibilidad
    index=True
)
```

#### 4.2 Modelos del Catálogo

```python
"""
Academic Catalog Models - Jerarquía Materia → Unidad

Estos modelos son OPCIONALES. El sistema funciona completamente
sin ellos. Solo se usan cuando el docente decide estructurar
su curso en materias y unidades.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, BigInteger, Integer, Text, DateTime, ForeignKey,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, BaseModel


class MateriaDB(BaseModel):
    """
    Asignatura o curso académico.

    Representa una materia completa (ej: "Programación I").
    Se relaciona con el course_name de UserDB para contexto académico.
    """
    __tablename__ = "materia"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_materia_codigo"),
        Index("idx_materia_nombre", "nombre"),
    )

    codigo: Mapped[str] = mapped_column(Text, nullable=False)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creditos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relaciones
    unidades = relationship("UnidadDB", back_populates="materia", cascade="all, delete-orphan")


class UnidadDB(BaseModel):
    """
    División temática dentro de una materia.

    Representa una unidad de estudio (ej: "Unidad 3: Estructuras de Control").
    Agrupa actividades y documentos relacionados temáticamente.
    """
    __tablename__ = "unidad"
    __table_args__ = (
        UniqueConstraint("materia_id", "numero", name="uq_unidad_materia_numero"),
        Index("idx_unidad_materia", "materia_id"),
    )

    materia_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("materia.id", ondelete="CASCADE"),
        nullable=False
    )
    numero: Mapped[int] = mapped_column(Integer, nullable=False)
    titulo: Mapped[str] = mapped_column(Text, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    objetivos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    orden: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relaciones
    materia = relationship("MateriaDB", back_populates="unidades")
    # Las actividades se relacionan via ActivityDB.unidad_id (opcional)
    # Los documentos se relacionan via UnidadDocumentoDB.unidad_id
```

#### 4.3 Repositorio del Catálogo

```python
"""
Catalog Repository - Operaciones de persistencia para el catálogo académico
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from .base import BaseRepository
from ..models.academic_catalog import MateriaDB, UnidadDB


class CatalogRepository(BaseRepository):
    """Repositorio para el catálogo académico."""

    def __init__(self, db: Session):
        super().__init__(db)

    # ==================== Materias ====================

    def create_materia(
        self,
        codigo: str,
        nombre: str,
        descripcion: Optional[str] = None,
        creditos: int = 0
    ) -> MateriaDB:
        """Crea una nueva materia."""
        materia = MateriaDB(
            codigo=codigo,
            nombre=nombre,
            descripcion=descripcion,
            creditos=creditos
        )
        self.db.add(materia)
        self.db.flush()
        return materia

    def get_materia_by_id(self, materia_id) -> Optional[MateriaDB]:
        """Obtiene una materia por su ID."""
        return self.db.get(MateriaDB, materia_id)

    def get_materia_by_codigo(self, codigo: str) -> Optional[MateriaDB]:
        """Obtiene una materia por su código."""
        return self.db.execute(
            select(MateriaDB).where(MateriaDB.codigo == codigo)
        ).scalar_one_or_none()

    def get_all_materias(self) -> List[MateriaDB]:
        """Obtiene todas las materias ordenadas."""
        return list(self.db.execute(
            select(MateriaDB).order_by(MateriaDB.orden.asc(), MateriaDB.nombre.asc())
        ).scalars().all())

    # ==================== Unidades ====================

    def create_unidad(
        self,
        materia_id: int,
        numero: int,
        titulo: str,
        descripcion: Optional[str] = None,
        objetivos: Optional[str] = None
    ) -> UnidadDB:
        """Crea una nueva unidad para una materia."""
        unidad = UnidadDB(
            materia_id=materia_id,
            numero=numero,
            titulo=titulo,
            descripcion=descripcion,
            objetivos=objetivos,
            orden=numero  # Por defecto, orden = número
        )
        self.db.add(unidad)
        self.db.flush()
        return unidad

    def get_unidad_by_id(self, unidad_id) -> Optional[UnidadDB]:
        """Obtiene una unidad por su ID."""
        return self.db.get(UnidadDB, unidad_id)

    def get_unidades_by_materia(self, materia_id: int) -> List[UnidadDB]:
        """Obtiene todas las unidades de una materia."""
        return list(self.db.execute(
            select(UnidadDB)
            .where(UnidadDB.materia_id == materia_id)
            .order_by(UnidadDB.orden.asc())
        ).scalars().all())

    def get_unidad_by_materia_numero(
        self,
        materia_id: int,
        numero: int
    ) -> Optional[UnidadDB]:
        """Obtiene una unidad específica por materia y número."""
        return self.db.execute(
            select(UnidadDB)
            .where(UnidadDB.materia_id == materia_id)
            .where(UnidadDB.numero == numero)
        ).scalar_one_or_none()
```

---

### Capítulo 5: Fase 3 — Patrón HU+CA para Ejercicios

Esta fase enriquece el modelo de ejercicios existente con el patrón de Historia de Usuario y Criterios de Aceptación, sin romper ejercicios existentes.

#### 5.1 Extensión del Modelo ExerciseDB

En lugar de crear tablas separadas (como propone rag1.txt), extendemos el modelo existente con campos opcionales:

```python
# Añadir a backend/database/models/exercise.py
# DESPUÉS de los campos existentes

# ===== Campos HU+CA (Cortez-RAG Integration) =====
# Todos los campos son OPCIONALES para compatibilidad con ejercicios existentes

historia_usuario: Mapped[Optional[str]] = mapped_column(
    Text,
    nullable=True,
    comment="Historia de Usuario en formato: Como [rol], quiero [acción], para [beneficio]"
)

criterios_aceptacion: Mapped[Optional[dict]] = mapped_column(
    JSONB,
    nullable=True,
    default=None,
    comment="Lista ordenada de criterios de aceptación: [{orden: 1, texto: '...', verificable: true}]"
)

contexto_pedagogico: Mapped[Optional[dict]] = mapped_column(
    JSONB,
    nullable=True,
    default=None,
    comment="Contexto adicional para RAG: conceptos_previos, errores_comunes, recursos_relacionados"
)
```

#### 5.2 Validadores para HU+CA

```python
# Añadir a backend/api/schemas/exercise.py

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class CriterioAceptacion(BaseModel):
    """Criterio de aceptación individual."""
    orden: int = Field(ge=1)
    texto: str = Field(min_length=5, max_length=500)
    verificable: bool = True

    @field_validator("texto")
    @classmethod
    def texto_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El criterio no puede estar vacío")
        return v


class HistoriaUsuario(BaseModel):
    """Historia de Usuario estructurada."""
    rol: str = Field(description="Como [rol]")
    accion: str = Field(description="quiero [acción]")
    beneficio: str = Field(description="para [beneficio]")

    def to_text(self) -> str:
        """Convierte a formato texto estándar."""
        return f"Como {self.rol}, quiero {self.accion}, para {self.beneficio}."

    @classmethod
    def from_text(cls, text: str) -> Optional["HistoriaUsuario"]:
        """Parsea desde formato texto."""
        import re
        pattern = r"Como\s+(.+?),\s+quiero\s+(.+?),\s+para\s+(.+?)\.?"
        match = re.match(pattern, text, re.IGNORECASE)
        if match:
            return cls(
                rol=match.group(1).strip(),
                accion=match.group(2).strip(),
                beneficio=match.group(3).strip()
            )
        return None


class ExerciseHUCAUpdate(BaseModel):
    """Schema para actualizar HU+CA de un ejercicio."""
    historia_usuario: Optional[str] = None
    criterios_aceptacion: Optional[List[CriterioAceptacion]] = None
    contexto_pedagogico: Optional[dict] = None
```

---

### Capítulo 6: Fase 4 — Integración RAG con AIGateway

Esta es la fase crítica donde el sistema RAG se conecta con el flujo de interacciones existente. El principio fundamental es que RAG **enriquece** el contexto pero nunca **reemplaza** la lógica de agentes.

#### 6.1 RAG Coordinator

Siguiendo el patrón de coordinadores establecido en Cortez66, creamos un coordinador RAG:

```python
"""
RAG Coordinator - Coordina retrieval y contexto RAG

Este coordinador se integra con AIGateway como una capa OPCIONAL
que enriquece el contexto de las interacciones.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

from ..database.repositories.rag_repository import RAGRepository
from ..services.embedding_service import EmbeddingProvider

logger = logging.getLogger(__name__)


@dataclass
class RAGContext:
    """Contexto recuperado por RAG."""
    chunks: List[Dict[str, Any]]
    query: str
    unidad_id: int
    total_retrieved: int
    avg_similarity: float

    def to_prompt_context(self, max_chars: int = 3000) -> str:
        """Convierte a texto para incluir en prompt."""
        if not self.chunks:
            return ""

        parts = []
        total_chars = 0

        for chunk in self.chunks:
            text = chunk["text"]
            if total_chars + len(text) > max_chars:
                # Truncar si excede límite
                remaining = max_chars - total_chars
                if remaining > 100:
                    text = text[:remaining] + "..."
                    parts.append(f"[Fuente: pág. {chunk.get('page_from', '?')}]\n{text}")
                break

            parts.append(f"[Fuente: pág. {chunk.get('page_from', '?')}]\n{text}")
            total_chars += len(text)

        return "\n\n---\n\n".join(parts)


class RAGCoordinator:
    """
    Coordina operaciones de RAG para el AIGateway.

    Responsabilidades:
    - Determinar si RAG debe usarse para una interacción
    - Ejecutar retrieval y construir contexto
    - Registrar eventos RAG en trazabilidad
    """

    def __init__(
        self,
        rag_repo: RAGRepository,
        embedding_provider: EmbeddingProvider,
        enabled: bool = False,
        top_k: int = 6,
        threshold: float = 0.7
    ):
        self.rag_repo = rag_repo
        self.embedder = embedding_provider
        self.enabled = enabled
        self.top_k = top_k
        self.threshold = threshold

    def should_use_rag(
        self,
        request: Dict[str, Any]
    ) -> bool:
        """
        Determina si RAG debe usarse para esta interacción.

        Condiciones:
        1. RAG está habilitado globalmente
        2. La interacción tiene unidad_id asociada
        3. Hay documentos disponibles para la unidad
        """
        if not self.enabled:
            return False

        unidad_id = request.get("unidad_id")
        if not unidad_id:
            return False

        # Verificar si hay documentos
        docs = self.rag_repo.get_documentos_by_unidad(unidad_id)
        return len(docs) > 0

    async def retrieve_context(
        self,
        query: str,
        unidad_id: int
    ) -> Optional[RAGContext]:
        """
        Ejecuta retrieval y construye contexto RAG.

        Returns:
            RAGContext si se encuentran chunks relevantes, None si no.
        """
        try:
            # Generar embedding de la consulta
            embeddings = await self.embedder.embed_texts([query])
            query_embedding = embeddings[0]

            # Buscar chunks similares
            chunks = self.rag_repo.get_similar_chunks(
                embedding=query_embedding,
                unidad_id=unidad_id,
                top_k=self.top_k,
                threshold=self.threshold
            )

            if not chunks:
                logger.debug(f"RAG: No se encontraron chunks para unidad {unidad_id}")
                return None

            # Calcular métricas
            avg_similarity = sum(c["similarity"] for c in chunks) / len(chunks)

            return RAGContext(
                chunks=chunks,
                query=query,
                unidad_id=unidad_id,
                total_retrieved=len(chunks),
                avg_similarity=avg_similarity
            )

        except Exception as e:
            logger.error(f"Error en RAG retrieval: {e}")
            return None

    def create_rag_event_payload(
        self,
        context: Optional[RAGContext],
        latency_ms: int
    ) -> Dict[str, Any]:
        """Crea payload para evento de trazabilidad RAG."""
        if context is None:
            return {
                "status": "no_results",
                "latency_ms": latency_ms
            }

        return {
            "status": "success",
            "unidad_id": context.unidad_id,
            "query": context.query[:200],  # Truncar para no sobrecargar
            "chunks_retrieved": context.total_retrieved,
            "avg_similarity": round(context.avg_similarity, 3),
            "latency_ms": latency_ms,
            "chunk_ids": [c["chunk_id"] for c in context.chunks]
        }
```

#### 6.2 Integración con AIGateway

La integración con el AIGateway existente sigue el principio de mínima intrusión:

```python
# Modificación a backend/core/ai_gateway.py
# AÑADIR después de las importaciones existentes

from .gateway.rag_coordinator import RAGCoordinator, RAGContext
from ..api.config import RAG_ENABLED

# AÑADIR en el constructor de AIGateway
def __init__(
    self,
    # ... parámetros existentes ...
    rag_coordinator: Optional[RAGCoordinator] = None,  # NUEVO
):
    # ... inicialización existente ...
    self._rag_coordinator = rag_coordinator  # NUEVO


# MODIFICAR process_interaction para incluir RAG
async def process_interaction(
    self,
    session_id: str,
    student_id: str,
    activity_id: str,
    student_prompt: str,
    cognitive_state: str,
    conversation_history: List[Dict],
    unidad_id: Optional[int] = None,  # NUEVO parámetro opcional
    **kwargs
) -> TutorResponse:
    """
    Procesa una interacción del estudiante.

    [Documentación existente...]

    Nuevo en RAG Integration:
    - Si unidad_id está presente y RAG está habilitado, se recupera
      contexto de documentos relevantes para enriquecer la respuesta.
    """
    import time

    # 1. CRPE clasifica el prompt (EXISTENTE - sin cambios)
    classification = self.cognitive_engine.classify(student_prompt, {
        "session_id": session_id,
        "cognitive_state": cognitive_state,
        "history_length": len(conversation_history)
    })

    # 2. NUEVO: RAG retrieval si está habilitado y hay unidad
    rag_context: Optional[RAGContext] = None
    if self._rag_coordinator and unidad_id:
        if self._rag_coordinator.should_use_rag({"unidad_id": unidad_id}):
            rag_start = time.time()
            rag_context = await self._rag_coordinator.retrieve_context(
                query=student_prompt,
                unidad_id=unidad_id
            )
            rag_latency = int((time.time() - rag_start) * 1000)

            # Registrar evento RAG en trazabilidad
            if self._trace_coordinator:
                await self._trace_coordinator.record_rag_event(
                    session_id=session_id,
                    payload=self._rag_coordinator.create_rag_event_payload(
                        rag_context, rag_latency
                    )
                )

    # 3. Construir contexto enriquecido (MODIFICADO)
    enriched_context = {
        "classification": classification,
        "cognitive_state": cognitive_state,
        "history": conversation_history,
    }

    # NUEVO: Añadir contexto RAG si existe
    if rag_context:
        enriched_context["rag_context"] = rag_context.to_prompt_context()
        enriched_context["rag_sources"] = [
            {"page": c["page_from"], "doc_id": c["documento_id"]}
            for c in rag_context.chunks
        ]

    # 4. Seleccionar estrategia y generar respuesta (EXISTENTE - sin cambios)
    strategy = self._mode_factory.create_strategy(
        mode=self._determine_mode(classification),
        cognitive_state=cognitive_state
    )

    response = await strategy.generate_response(
        prompt=student_prompt,
        context=enriched_context,
        llm=self._llm_provider
    )

    # 5. Trazabilidad y riesgos (EXISTENTE - sin cambios)
    await self._trace_coordinator.record(...)
    await self._risk_coordinator.analyze(...)

    return response
```

#### 6.3 Modificación de Prompts del Tutor

Para que el contexto RAG se use efectivamente, los prompts del tutor deben modificarse para incorporarlo:

```python
# Añadir a backend/agents/tutor/prompts.py

RAG_CONTEXT_SECTION = """
## Contexto de Documentos del Curso

El siguiente contenido proviene de los materiales del curso y es relevante para la consulta del estudiante:

{rag_context}

INSTRUCCIONES PARA USAR ESTE CONTEXTO:
1. Usa esta información para fundamentar tu respuesta
2. Si citas directamente, indica la fuente (página)
3. No inventes información que no esté en el contexto
4. Si el contexto no es suficiente, indica que el estudiante puede consultar otros materiales
"""


def build_tutor_prompt(
    base_prompt: str,
    rag_context: Optional[str] = None,
    **kwargs
) -> str:
    """
    Construye el prompt final del tutor incluyendo contexto RAG si está disponible.

    Esta función NO modifica el prompt base existente; solo AÑADE
    la sección RAG cuando hay contexto disponible.
    """
    sections = [base_prompt]

    if rag_context:
        sections.append(RAG_CONTEXT_SECTION.format(rag_context=rag_context))

    return "\n\n".join(sections)
```

---

### Capítulo 7: Fase 5 — Event Sourcing Complementario

Esta fase añade el modelo de eventos atómicos de IA como complemento a la trazabilidad N4 existente.

#### 7.1 Modelo de Eventos

```python
"""
AI Event Model - Eventos atómicos de interacción con IA

Este modelo COMPLEMENTA (no reemplaza) la trazabilidad N4.
- ai_event: Captura eventos atómicos (PROMPT, RETRIEVAL, RESPONSE, etc.)
- CognitiveTraceDB: Mantiene análisis cognitivo agregado

La relación es:
- Múltiples ai_event pueden corresponder a un CognitiveTrace
- ai_event proporciona auditoría detallada
- CognitiveTrace proporciona análisis pedagógico
"""

import enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, BigInteger, Text, DateTime, ForeignKey, Index, Enum
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
import uuid

from .base import Base


class AIEventType(str, enum.Enum):
    """Tipos de eventos de IA."""
    PROMPT_SUBMITTED = "PROMPT_SUBMITTED"
    RAG_RETRIEVAL = "RAG_RETRIEVAL"
    MODEL_RESPONSE = "MODEL_RESPONSE"
    CODE_SNAPSHOT = "CODE_SNAPSHOT"
    EVAL_REQUESTED = "EVAL_REQUESTED"
    EVAL_RESULT = "EVAL_RESULT"
    RISK_FLAGGED = "RISK_FLAGGED"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"
    HINT_REQUESTED = "HINT_REQUESTED"
    REFLECTION_CAPTURED = "REFLECTION_CAPTURED"


class AIEventDB(Base):
    """
    Evento atómico de interacción con IA.

    Cada evento captura un momento específico en la interacción:
    - Cuándo el estudiante envió un prompt
    - Cuándo el sistema recuperó documentos (RAG)
    - Cuándo el LLM generó una respuesta
    - Cuándo se detectó un riesgo

    Esto permite reconstruir la secuencia completa de eventos
    para auditoría y debugging.
    """
    __tablename__ = "ai_event"
    __table_args__ = (
        Index("idx_ai_event_session", "sesion_id", "created_at"),
        Index("idx_ai_event_student", "estudiante_id", "created_at"),
        Index("idx_ai_event_type", "event_type"),
        Index("idx_ai_event_ejercicio", "ejercicio_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    estudiante_id: Mapped[str] = mapped_column(Text, nullable=False)
    sesion_id: Mapped[str] = mapped_column(Text, nullable=False)
    ejercicio_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    trace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Referencia al CognitiveTraceDB asociado, si existe"
    )
    event_type: Mapped[AIEventType] = mapped_column(
        Enum(AIEventType),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict
    )
```

#### 7.2 Sincronización con Trazabilidad N4

El coordinador de trazas se extiende para crear eventos atómicos además de los traces agregados:

```python
# Añadir a backend/core/gateway/trace_coordinator.py

async def record_with_events(
    self,
    session_id: str,
    student_id: str,
    request: Dict[str, Any],
    response: Dict[str, Any],
    classification: Dict[str, Any],
    rag_context: Optional[Dict] = None
) -> str:
    """
    Registra interacción en trazabilidad N4 Y eventos atómicos.

    Esta función mantiene sincronizados ambos sistemas:
    1. Crea el CognitiveTrace con análisis agregado
    2. Crea eventos atómicos para cada paso del procesamiento

    Returns:
        trace_id del CognitiveTrace creado
    """
    # 1. Crear trace N4 (existente)
    trace_id = await self.record(
        session_id=session_id,
        student_id=student_id,
        request=request,
        response=response,
        classification=classification
    )

    # 2. Crear eventos atómicos (nuevo)
    events = []

    # Evento: Prompt recibido
    events.append({
        "estudiante_id": student_id,
        "sesion_id": session_id,
        "trace_id": trace_id,
        "event_type": AIEventType.PROMPT_SUBMITTED,
        "payload": {
            "prompt": request.get("prompt", "")[:500],
            "cognitive_state": classification.get("cognitive_state"),
            "signals_detected": classification.get("signals", [])[:10]
        }
    })

    # Evento: RAG retrieval (si hubo)
    if rag_context:
        events.append({
            "estudiante_id": student_id,
            "sesion_id": session_id,
            "trace_id": trace_id,
            "event_type": AIEventType.RAG_RETRIEVAL,
            "payload": rag_context
        })

    # Evento: Respuesta del modelo
    events.append({
        "estudiante_id": student_id,
        "sesion_id": session_id,
        "trace_id": trace_id,
        "event_type": AIEventType.MODEL_RESPONSE,
        "payload": {
            "response_type": response.get("type"),
            "response_length": len(response.get("content", "")),
            "mode_used": response.get("mode")
        }
    })

    # Persistir eventos
    for event_data in events:
        self._event_repo.create(AIEventDB(**event_data))

    return trace_id
```

---

### Capítulo 8: Fase 6 — MinIO para Storage de Documentos

Esta fase introduce almacenamiento de objetos para PDFs y entregas, separando archivos binarios de la base de datos.

#### 8.1 Servicio de Storage Abstracto

```python
"""
Storage Service - Abstracción para almacenamiento de archivos

Soporta:
- FileSystem local (desarrollo)
- MinIO (producción)

El código consumidor usa la interfaz abstracta, permitiendo
cambiar la implementación sin modificar la lógica de negocio.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
import os
import io
import hashlib
from minio import Minio
from minio.error import S3Error


class StorageProvider(ABC):
    """Interfaz abstracta para proveedores de storage."""

    @abstractmethod
    def upload(
        self,
        key: str,
        data: BinaryIO,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Sube un archivo y retorna la key."""
        pass

    @abstractmethod
    def download(self, key: str) -> bytes:
        """Descarga un archivo por su key."""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Elimina un archivo. Retorna True si existía."""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verifica si un archivo existe."""
        pass

    @abstractmethod
    def get_url(self, key: str, expires_seconds: int = 3600) -> Optional[str]:
        """Genera URL temporal de acceso (si aplica)."""
        pass


class LocalStorageProvider(StorageProvider):
    """
    Proveedor de storage usando sistema de archivos local.

    Útil para desarrollo y testing. NO usar en producción.
    """

    def __init__(self, base_path: str = "./storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _full_path(self, key: str) -> str:
        # Sanitizar key para evitar path traversal
        safe_key = key.replace("..", "").lstrip("/")
        path = os.path.join(self.base_path, safe_key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def upload(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        path = self._full_path(key)
        with open(path, "wb") as f:
            f.write(data.read())
        return key

    def download(self, key: str) -> bytes:
        path = self._full_path(key)
        with open(path, "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        path = self._full_path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    def get_url(self, key: str, expires_seconds: int = 3600) -> Optional[str]:
        # Local storage no soporta URLs temporales
        return None


class MinIOStorageProvider(StorageProvider):
    """
    Proveedor de storage usando MinIO (S3-compatible).

    Configuración via variables de entorno:
    - MINIO_ENDPOINT
    - MINIO_ACCESS_KEY
    - MINIO_SECRET_KEY
    - MINIO_BUCKET
    - MINIO_SECURE
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "activia",
        secure: bool = False
    ):
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Crea el bucket si no existe."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            raise RuntimeError(f"Error creando bucket MinIO: {e}")

    def upload(self, key: str, data: BinaryIO, content_type: str = "application/octet-stream") -> str:
        # Obtener tamaño del archivo
        data.seek(0, 2)
        size = data.tell()
        data.seek(0)

        self.client.put_object(
            bucket_name=self.bucket,
            object_name=key,
            data=data,
            length=size,
            content_type=content_type
        )
        return key

    def download(self, key: str) -> bytes:
        response = self.client.get_object(self.bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> bool:
        try:
            self.client.remove_object(self.bucket, key)
            return True
        except S3Error:
            return False

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except S3Error:
            return False

    def get_url(self, key: str, expires_seconds: int = 3600) -> Optional[str]:
        """Genera URL pre-firmada para acceso temporal."""
        from datetime import timedelta
        try:
            return self.client.presigned_get_object(
                self.bucket,
                key,
                expires=timedelta(seconds=expires_seconds)
            )
        except S3Error:
            return None


# Factory para crear el proveedor según configuración
def create_storage_provider() -> StorageProvider:
    """Crea el proveedor de storage según configuración."""
    provider_type = os.getenv("STORAGE_PROVIDER", "local")

    if provider_type == "local":
        return LocalStorageProvider(
            base_path=os.getenv("STORAGE_LOCAL_PATH", "./storage")
        )
    elif provider_type == "minio":
        return MinIOStorageProvider(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            bucket=os.getenv("MINIO_BUCKET", "activia"),
            secure=os.getenv("MINIO_SECURE", "false").lower() == "true"
        )
    else:
        raise ValueError(f"Proveedor de storage no soportado: {provider_type}")
```

#### 8.2 Docker Compose para MinIO

```yaml
# Añadir a docker-compose.yml o crear docker-compose.minio.yml

services:
  minio:
    image: minio/minio:latest
    container_name: activia-minio
    ports:
      - "9000:9000"    # API
      - "9001:9001"    # Console
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

volumes:
  minio_data:
```

---

## Parte III: Verificación y Mantenimiento

### Capítulo 9: Tests de Integración RAG

#### 9.1 Tests de Repositorio

```python
"""
Tests para RAGRepository

Verifican que las operaciones de persistencia funcionan correctamente
y que la búsqueda vectorial retorna resultados relevantes.
"""

import pytest
from unittest.mock import MagicMock
import numpy as np

from backend.database.repositories.rag_repository import RAGRepository
from backend.database.models.rag import DocumentoChunkDB


@pytest.fixture
def mock_embedding():
    """Genera un embedding de prueba normalizado."""
    vec = np.random.randn(384)
    return (vec / np.linalg.norm(vec)).tolist()


class TestRAGRepository:

    def test_create_documento(self, db_session):
        """Verifica creación de documento."""
        repo = RAGRepository(db_session)

        doc = repo.create_documento(
            unidad_id=1,
            tipo="MATERIAL",
            titulo="Test Document",
            storage_key="test/doc.pdf",
            sha256="abc123",
            size_bytes=1024
        )

        assert doc.id is not None
        assert doc.tipo == "MATERIAL"
        assert doc.estado == "BORRADOR"

    def test_get_similar_chunks(self, db_session, mock_embedding):
        """Verifica búsqueda por similitud."""
        repo = RAGRepository(db_session)

        # Crear chunks de prueba con embeddings similares
        # ...

        results = repo.get_similar_chunks(
            embedding=mock_embedding,
            unidad_id=1,
            top_k=5,
            threshold=0.5
        )

        assert isinstance(results, list)
        for r in results:
            assert "chunk_id" in r
            assert "text" in r
            assert "similarity" in r
            assert 0 <= r["similarity"] <= 1


class TestRAGIntegration:
    """Tests de integración con el sistema existente."""

    @pytest.mark.parametrize("rag_enabled", [False, True])
    async def test_gateway_with_rag_flag(
        self,
        test_client,
        rag_enabled,
        monkeypatch
    ):
        """
        Verifica que el gateway funciona correctamente
        independientemente del estado del flag RAG.
        """
        monkeypatch.setenv("RAG_ENABLED", str(rag_enabled).lower())

        # Crear sesión
        response = await test_client.post("/api/v1/sessions/", json={
            "student_id": "test-student",
            "activity_id": "test-activity",
            "mode": "TUTOR"
        })
        assert response.status_code == 201
        session_id = response.json()["id"]

        # Enviar interacción
        response = await test_client.post("/api/v1/interactions/", json={
            "session_id": session_id,
            "prompt": "¿Cómo funcionan los loops en Python?"
        })
        assert response.status_code == 200
        assert "response" in response.json()
```

#### 9.2 Tests de No Regresión

```python
"""
Tests de No Regresión

Verifican que las funcionalidades existentes siguen funcionando
después de añadir RAG.
"""

import pytest


class TestNoRegression:
    """Tests que verifican que nada se rompió."""

    async def test_tutor_modes_unchanged(self, test_client, db_session):
        """Los 5 modos del tutor siguen funcionando."""
        modes = ["socratic", "explicative", "guided", "metacognitive", "training_hints"]

        for mode in modes:
            # Crear sesión en cada modo
            # Enviar interacción
            # Verificar respuesta apropiada para el modo
            pass

    async def test_risk_analysis_unchanged(self, test_client, db_session):
        """El análisis de riesgos 5D sigue funcionando."""
        # Crear sesión con patrones de delegación
        # Verificar que se detectan los riesgos
        pass

    async def test_n4_traceability_unchanged(self, test_client, db_session):
        """La trazabilidad N4 sigue funcionando."""
        # Crear interacciones
        # Verificar que se crean traces con 6 dimensiones
        pass

    async def test_training_v1_endpoints_unchanged(self, test_client):
        """Los endpoints V1 de training siguen funcionando."""
        # GET /training/lenguajes
        # POST /training/iniciar
        # POST /training/submit-ejercicio
        pass

    async def test_simulators_unchanged(self, test_client):
        """Los 11 simuladores profesionales siguen funcionando."""
        simulators = [
            "product_owner", "scrum_master", "tech_interviewer",
            "incident_responder", "devsecops", "client"
        ]
        for sim in simulators:
            # Iniciar sesión de simulador
            # Enviar interacción
            # Verificar respuesta apropiada
            pass
```

---

### Capítulo 10: Checklist de Implementación

#### 10.1 Pre-requisitos

- [ ] PostgreSQL 15+ con extensión pgvector instalable
- [ ] Docker y Docker Compose actualizados
- [ ] Ollama instalado con modelo nomic-embed-text
- [ ] Branch `feature/rag-integration` creado desde main
- [ ] Tests existentes pasando (baseline)

#### 10.2 Fase 1 Checklist

- [ ] Migración pgvector ejecutada exitosamente
- [ ] Modelos RAG creados y validados
- [ ] Repositorio RAG con tests unitarios
- [ ] Servicio de embeddings funcionando
- [ ] Feature flag `RAG_ENABLED=false` por defecto
- [ ] Tests de no regresión pasando

#### 10.3 Fase 2 Checklist

- [ ] Modelos MateriaDB y UnidadDB creados
- [ ] Repositorio CatalogRepository implementado
- [ ] ActivityDB.unidad_id añadido (nullable)
- [ ] Migración ejecutada sin pérdida de datos
- [ ] Actividades existentes siguen funcionando

#### 10.4 Fase 3 Checklist

- [ ] Campos HU+CA añadidos a ExerciseDB
- [ ] Validadores Pydantic implementados
- [ ] Ejercicios existentes sin HU/CA siguen funcionando
- [ ] Tests de schemas pasando

#### 10.5 Fase 4 Checklist

- [ ] RAGCoordinator implementado
- [ ] AIGateway modificado con integración RAG
- [ ] Prompts del tutor actualizados
- [ ] Tests de integración pasando
- [ ] Métricas de latencia aceptables (<500ms adicionales)

#### 10.6 Fase 5 Checklist

- [ ] Modelo AIEventDB creado
- [ ] Eventos sincronizados con trazas N4
- [ ] Queries de auditoría funcionando
- [ ] No duplicación de datos entre sistemas

#### 10.7 Fase 6 Checklist

- [ ] MinIO desplegado y funcionando
- [ ] StorageService abstraído correctamente
- [ ] Upload/download de PDFs funcionando
- [ ] URLs temporales generándose correctamente
- [ ] Cleanup de archivos huérfanos implementado

---

## Conclusión

La implementación de RAG en el sistema AI-Native MVP es una empresa significativa pero enteramente factible cuando se aborda con disciplina arquitectónica. El principio rector de esta guía ha sido la no regresión: cada cambio se diseña para añadir capacidades sin comprometer las existentes.

Los seis agentes de inteligencia artificial, la trazabilidad cognitiva de cuatro niveles, los once simuladores profesionales, y el análisis de riesgos de cinco dimensiones representan una inversión enorme de desarrollo y refinamiento a lo largo de más de setenta auditorías de calidad. Cualquier integración RAG debe respetar y aprovechar esta infraestructura, no reemplazarla.

La estrategia de fases permite validación continua. Cada fase produce un sistema funcional que puede desplegarse a producción con feature flags desactivados. Esto minimiza el riesgo y permite aprendizaje incremental sobre cómo el RAG interactúa con los patrones de uso reales del sistema.

El resultado final será un sistema que combina lo mejor de ambos mundos: la sofisticación pedagógica de los agentes existentes con la capacidad de retrieval semántico de documentos que proporciona RAG. Los estudiantes recibirán respuestas fundamentadas en los materiales del curso, mientras que los docentes tendrán trazabilidad completa de cómo el sistema usa sus materiales para asistir el aprendizaje.

---

*Documento técnico para implementación de RAG en AI-Native MVP.*
*Actualizar según se completen las fases de implementación.*
