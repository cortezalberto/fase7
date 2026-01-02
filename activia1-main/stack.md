# Propuesta de Stack Tecnologico para la Arquitectura Multi-Agente Active-IA

## Documento de Recomendacion Tecnica y Economica

**Version**: 1.0
**Fecha**: Enero 2026
**Referencia**: `backend/ImplementacionAgentes.md`

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Analisis del Stack Actual](#2-analisis-del-stack-actual)
3. [Base de Datos Vectorial: Propuesta y Justificacion](#3-base-de-datos-vectorial-propuesta-y-justificacion)
4. [Proveedor de Embeddings](#4-proveedor-de-embeddings)
5. [Proveedor LLM: Optimizacion de Costos](#5-proveedor-llm-optimizacion-de-costos)
6. [Infraestructura de Cache y Mensajeria](#6-infraestructura-de-cache-y-mensajeria)
7. [Observabilidad y Monitoreo](#7-observabilidad-y-monitoreo)
8. [Seguridad y Cumplimiento](#8-seguridad-y-cumplimiento)
9. [Estimacion de Costos](#9-estimacion-de-costos)
10. [Arquitectura de Despliegue](#10-arquitectura-de-despliegue)
11. [Plan de Implementacion](#11-plan-de-implementacion)
12. [Alternativas Evaluadas](#12-alternativas-evaluadas)

---

## 1. Resumen Ejecutivo

La arquitectura multi-agente Active-IA propuesta en `ImplementacionAgentes.md` introduce seis agentes especializados que requieren capacidades tecnologicas especificas, particularmente en el area de recuperacion de conocimiento (RAG) y procesamiento de lenguaje natural. Este documento presenta una propuesta de stack tecnologico optimizada para costos, manteniendo la calidad pedagogica requerida por un proyecto de tesis doctoral.

### 1.1 Principios Rectores de la Propuesta

La seleccion tecnologica se guia por cuatro principios fundamentales:

**Principio 1: Economia sin Sacrificar Calidad**. El proyecto es una tesis doctoral, no un producto comercial con ingresos. Cada componente debe justificar su costo en terminos de valor pedagogico. Preferimos soluciones open-source y self-hosted donde sea posible, recurriendo a servicios cloud solo cuando el costo de operacion propia exceda el beneficio.

**Principio 2: Compatibilidad con Infraestructura Existente**. El sistema ya cuenta con PostgreSQL, Redis, FastAPI y React funcionando correctamente. Cualquier nueva tecnologia debe integrarse sin requerir migraciones costosas o cambios arquitectonicos disruptivos.

**Principio 3: Escalabilidad Gradual**. La solucion debe funcionar en un laptop de desarrollo durante la fase de tesis, pero permitir escalado a multiples usuarios (curso de 30-50 estudiantes) sin rediseno. El costo debe escalar proporcionalmente al uso.

**Principio 4: Simplicidad Operativa**. Un proyecto de tesis no tiene equipo de DevOps dedicado. Las tecnologias seleccionadas deben ser mantenibles por un desarrollador individual, con documentacion clara y comunidad activa.

### 1.2 Resumen de la Propuesta

| Componente | Tecnologia Recomendada | Costo Mensual Estimado |
|------------|------------------------|------------------------|
| Base de Datos Vectorial | **PostgreSQL + pgvector** | $0 (incluido en PostgreSQL existente) |
| Embeddings | **Ollama + nomic-embed-text** | $0 (self-hosted) |
| LLM Principal | **Mistral Small (API)** | ~$5-15/mes |
| LLM Backup/Fallback | **Ollama + phi3** | $0 (self-hosted) |
| Cache | **Redis** (existente) | $0 (incluido) |
| Monitoreo | **Prometheus + Grafana** (existente) | $0 (incluido) |
| **Total Estimado** | | **~$5-20/mes** |

---

## 2. Analisis del Stack Actual

### 2.1 Componentes Existentes

El proyecto ya cuenta con una infraestructura robusta que debe aprovecharse al maximo:

**Backend (Python 3.11+ / FastAPI)**:
```
pydantic>=2.6.0           # Validacion de datos
fastapi>=0.109.0          # Framework API
sqlalchemy>=2.0.25        # ORM
psycopg2-binary>=2.9.9    # Adaptador PostgreSQL
redis>=5.0.0              # Cliente Redis
httpx>=0.26.0             # Cliente HTTP async
prometheus-client>=0.19.0 # Metricas
```

**Frontend (React 19 / TypeScript 5.7)**:
```json
{
  "react": "^19.0.0",
  "@tanstack/react-query": "^5.62.0",
  "zustand": "^5.0.2",
  "axios": "^1.7.9",
  "tailwindcss": "^3.4.17"
}
```

**Infraestructura (Docker Compose)**:
- PostgreSQL 15.7-alpine
- Redis 7.2-alpine
- Prometheus 2.48.0
- Grafana 10.2.0

### 2.2 Proveedores LLM Configurados

El sistema actualmente soporta multiples proveedores LLM mediante una fabrica abstracta:

| Proveedor | Modelo Default | Estado |
|-----------|----------------|--------|
| Mistral API | mistral-small-latest | **Activo (produccion)** |
| Gemini API | gemini-2.5-flash | Configurado (backup) |
| Ollama | phi3 / mistral:7b | Desactivado (opcional) |
| OpenAI | gpt-3.5-turbo | Configurado (no usado) |

### 2.3 Brechas Tecnologicas Identificadas

Para implementar la arquitectura de seis agentes, faltan los siguientes componentes:

1. **Base de datos vectorial**: No existe almacenamiento de embeddings para RAG
2. **Servicio de embeddings**: No hay generacion de vectores para busqueda semantica
3. **Corpus de conocimiento**: No existe contenido academico estructurado
4. **Pipeline de ingesta**: No hay proceso para cargar documentos al vector store

---

## 3. Base de Datos Vectorial: Propuesta y Justificacion

### 3.1 Recomendacion: PostgreSQL + pgvector

La propuesta definitiva es utilizar **PostgreSQL con la extension pgvector** como base de datos vectorial. Esta decision se fundamenta en multiples factores economicos, tecnicos y operativos.

### 3.2 Justificacion Economica

**Costo de pgvector: $0 adicional**. La extension pgvector es open-source (licencia PostgreSQL) y se ejecuta dentro del PostgreSQL existente. No requiere infraestructura adicional, licencias, ni servicios cloud separados.

**Comparativa de costos mensuales**:

| Solucion | Costo Base | Costo por 10K docs | Costo por 100K docs |
|----------|------------|-------------------|---------------------|
| **pgvector** | $0 | $0 | $0 |
| ChromaDB (self-hosted) | $0 | $0 | $0 |
| Pinecone Starter | $0 | $0 | $0 (limite 100K) |
| Pinecone Standard | $70/mes | $70/mes | $70/mes |
| Weaviate Cloud | $25/mes | $25/mes | $50/mes |
| Qdrant Cloud | $25/mes | $25/mes | $50/mes |
| Milvus Cloud | $65/mes | $65/mes | $100/mes |

Para un proyecto academico con un corpus de documentos de catedra (estimado: 500-2,000 documentos), pgvector es la opcion mas economica y suficiente.

### 3.3 Justificacion Tecnica

**Ventaja 1: Infraestructura Unificada**. El proyecto ya utiliza PostgreSQL para datos relacionales (sesiones, trazas, usuarios, evaluaciones). Agregar pgvector elimina la complejidad de mantener dos sistemas de bases de datos.

**Ventaja 2: Transacciones ACID**. A diferencia de bases vectoriales especializadas, PostgreSQL garantiza transacciones atomicas. Esto es critico para la trazabilidad N4: cuando se registra una interaccion, tanto los datos relacionales como los embeddings se guardan en la misma transaccion.

**Ventaja 3: Queries Hibridas**. pgvector permite combinar busqueda vectorial con filtros SQL tradicionales en una sola query:

```sql
-- Buscar documentos similares, filtrados por unidad y dificultad
SELECT content, source_id,
       1 - (embedding <=> query_embedding) AS similarity
FROM knowledge_documents
WHERE unit = 'algoritmos_ordenamiento'
  AND difficulty <= 'intermedio'
  AND content_type IN ('teoria', 'ejemplo')
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

Esta capacidad es imposible o muy costosa en bases vectoriales puras como Pinecone, donde los filtros de metadatos tienen limitaciones.

**Ventaja 4: Indices Optimizados**. pgvector soporta dos tipos de indices:

- **IVFFlat**: Rapido para datasets pequenos-medianos (<1M vectores). Ideal para el proyecto.
- **HNSW**: Mejor precision para datasets grandes. Disponible si el corpus crece.

```sql
-- Indice IVFFlat para busqueda rapida
CREATE INDEX ON knowledge_documents
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Alternativa HNSW para mayor precision
CREATE INDEX ON knowledge_documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### 3.4 Justificacion Operativa

**Simplicidad de Deployment**. Agregar pgvector requiere solo dos pasos:

```dockerfile
# En Dockerfile de PostgreSQL
FROM postgres:15.7-alpine
RUN apk add --no-cache postgresql15-pgvector
```

```sql
-- En migracion de base de datos
CREATE EXTENSION IF NOT EXISTS vector;
```

No hay servicios adicionales que iniciar, monitorear, o escalar. El backup de PostgreSQL (pg_dump) incluye automaticamente los datos vectoriales.

**Integracion con SQLAlchemy**. Existe soporte nativo para pgvector en el ORM:

```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    content_type = Column(String(50))  # teoria, ejemplo, faq, consigna
    unit = Column(String(100))
    difficulty = Column(String(20))
    embedding = Column(Vector(384))  # Dimension de nomic-embed-text
    source_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 3.5 Limitaciones y Mitigaciones

**Limitacion 1: Rendimiento a Gran Escala**. pgvector es mas lento que bases especializadas para millones de vectores.

*Mitigacion*: El corpus academico de una catedra universitaria raramente excede 10,000 documentos. pgvector maneja este volumen sin problemas. Si el proyecto crece a escala institucional (multiples catedras), se puede migrar a Qdrant o Milvus sin cambiar la logica de aplicacion.

**Limitacion 2: No Tiene Busqueda Hibrida Nativa**. Bases como Weaviate combinan busqueda vectorial + keyword (BM25) automaticamente.

*Mitigacion*: PostgreSQL tiene `pg_trgm` para busqueda de texto. Se puede implementar busqueda hibrida manualmente:

```sql
-- Busqueda hibrida: 70% semantica + 30% keyword
SELECT *,
       0.7 * (1 - (embedding <=> query_embedding)) +
       0.3 * similarity(content, 'ordenamiento burbuja') AS score
FROM knowledge_documents
ORDER BY score DESC
LIMIT 5;
```

### 3.6 Modelo de Datos Propuesto

```sql
-- Migracion: Crear tabla de documentos de conocimiento
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Contenido
    content TEXT NOT NULL,
    title VARCHAR(255),
    summary TEXT,

    -- Clasificacion pedagogica
    content_type VARCHAR(50) NOT NULL,  -- teoria, ejemplo, faq, consigna, ejercicio
    unit VARCHAR(100),                   -- unidad tematica
    topic VARCHAR(100),                  -- tema especifico
    difficulty VARCHAR(20),              -- basico, intermedio, avanzado
    language VARCHAR(10) DEFAULT 'es',   -- idioma

    -- Embedding
    embedding vector(384),               -- nomic-embed-text dimension

    -- Trazabilidad
    source_id VARCHAR(255),              -- ID de documento original
    source_file VARCHAR(500),            -- Ruta del archivo fuente
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Metadatos adicionales
    metadata JSONB DEFAULT '{}'
);

-- Indices
CREATE INDEX idx_knowledge_embedding
    ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX idx_knowledge_unit ON knowledge_documents(unit);
CREATE INDEX idx_knowledge_type ON knowledge_documents(content_type);
CREATE INDEX idx_knowledge_difficulty ON knowledge_documents(difficulty);
CREATE INDEX idx_knowledge_metadata ON knowledge_documents USING gin(metadata);
```

---

## 4. Proveedor de Embeddings

### 4.1 Recomendacion: Ollama + nomic-embed-text

Para la generacion de embeddings, la propuesta es utilizar **Ollama con el modelo nomic-embed-text**. Esta combinacion ofrece el mejor balance entre costo, calidad y simplicidad.

### 4.2 Justificacion de la Seleccion

**Costo: $0**. Ollama es open-source y nomic-embed-text es un modelo gratuito. No hay costos por llamada a API ni limites de uso.

**Calidad**. nomic-embed-text es un modelo de embeddings de 384 dimensiones que logra resultados comparables a modelos comerciales:

| Modelo | Dimensiones | MTEB Score | Costo por 1M tokens |
|--------|-------------|------------|---------------------|
| **nomic-embed-text** | 384 | 62.3 | **$0** |
| OpenAI text-embedding-3-small | 1536 | 62.3 | $0.02 |
| OpenAI text-embedding-3-large | 3072 | 64.6 | $0.13 |
| Cohere embed-v3 | 1024 | 64.5 | $0.10 |
| Voyage-2 | 1024 | 66.8 | $0.10 |

Para busqueda de documentos educativos en espanol, la diferencia de 2-4 puntos en MTEB no es significativa. Los textos academicos tienen vocabulario especifico que beneficia mas de un corpus bien estructurado que de un modelo marginalmente mejor.

**Tamano Compacto**. Con 384 dimensiones (vs 1536 de OpenAI), los embeddings ocupan 75% menos espacio en la base de datos. Para 10,000 documentos:

- nomic-embed-text: ~15 MB
- OpenAI large: ~120 MB

**Latencia Local**. Al ejecutarse localmente, nomic-embed-text tiene latencia de 10-50ms por documento, sin dependencia de red externa ni rate limits.

### 4.3 Instalacion y Configuracion

```bash
# Instalar Ollama (si no esta instalado)
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo de embeddings
ollama pull nomic-embed-text

# Verificar instalacion
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Ordenamiento burbuja en Python"
}'
```

### 4.4 Integracion con el Backend

```python
# backend/core/embeddings.py
import httpx
from typing import List
import asyncio

class OllamaEmbeddingProvider:
    """
    Proveedor de embeddings usando Ollama con nomic-embed-text.

    Caracteristicas:
    - Costo: $0 (self-hosted)
    - Dimensiones: 384
    - Latencia: 10-50ms por documento
    - Sin rate limits
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 30.0
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client

    async def embed(self, text: str) -> List[float]:
        """Genera embedding para un texto."""
        client = await self._get_client()
        response = await client.post(
            "/api/embeddings",
            json={"model": self.model, "prompt": text}
        )
        response.raise_for_status()
        return response.json()["embedding"]

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Genera embeddings para multiples textos.

        Procesa en batches para evitar sobrecarga.
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.embed(text) for text in batch]
            )
            embeddings.extend(batch_embeddings)
        return embeddings

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
```

### 4.5 Alternativa para Produccion: API de Embeddings

Si en el futuro se requiere mayor rendimiento o el servidor no tiene GPU, se puede migrar a embeddings via API sin cambiar la logica:

```python
# backend/core/embeddings.py (alternativa cloud)
class MistralEmbeddingProvider:
    """
    Alternativa usando Mistral Embeddings API.

    Costo: $0.1 por 1M tokens (~$0.01 por 1000 documentos)
    """

    def __init__(self, api_key: str, model: str = "mistral-embed"):
        self.api_key = api_key
        self.model = model
        self.endpoint = "https://api.mistral.ai/v1/embeddings"

    async def embed(self, text: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text}
            )
            return response.json()["data"][0]["embedding"]
```

---

## 5. Proveedor LLM: Optimizacion de Costos

### 5.1 Estrategia de Multiples Modelos

La arquitectura de seis agentes tiene requisitos de LLM diferenciados. No todos los agentes necesitan el modelo mas potente. La propuesta es una estrategia de **modelos escalonados** que minimiza costos sin sacrificar calidad pedagogica.

### 5.2 Clasificacion de Agentes por Requisitos

| Agente | Complejidad | Modelo Recomendado | Justificacion |
|--------|-------------|-------------------|---------------|
| **CRPE/Gatekeeper** | Baja | Reglas + phi3 local | Clasificacion basica, no requiere razonamiento complejo |
| **Knowledge-Retrieval** | N/A | Solo embeddings | No usa LLM, solo busqueda vectorial |
| **T-IA-Cog (Tutor)** | Alta | Mistral Small API | Genera respuestas pedagogicas, requiere coherencia |
| **Fallback Pedagogico** | Media | phi3 local | Explicaciones generales, menos critico |
| **Safety & Governance** | Baja | Reglas + phi3 local | Validacion, puede ser heuristico |
| **Scaffolding** | Media | phi3 local / Mistral Small | Depende de complejidad del andamiaje |

### 5.3 Costo Optimizado por Uso

**Escenario: Sesion de 1 hora con 20 interacciones**

| Componente | Llamadas API | Tokens Estimados | Costo (Mistral Small) |
|------------|--------------|------------------|----------------------|
| Gatekeeper | 20 | 0 (local) | $0 |
| RAG | 20 | 0 (solo embeddings) | $0 |
| Tutor (Mistral) | 15 | ~30,000 | ~$0.006 |
| Fallback (local) | 3 | 0 (phi3) | $0 |
| Safety (local) | 20 | 0 (heuristico) | $0 |
| Scaffolding (local) | 5 | 0 (phi3) | $0 |
| **Total por sesion** | | | **~$0.006** |

**Costo mensual estimado** (30 estudiantes, 4 sesiones/semana):
- 30 estudiantes x 4 sesiones x 4 semanas = 480 sesiones
- 480 x $0.006 = **~$3/mes**

Con margen de seguridad (picos de uso, sesiones largas): **$5-15/mes**

### 5.4 Configuracion de Fallback en Cadena

```python
# backend/llm/factory.py (modificacion propuesta)
class LLMProviderFactory:
    """
    Fabrica con fallback en cadena para optimizar costos.

    Orden de fallback:
    1. Ollama (phi3) - Gratis, local
    2. Mistral Small API - Barato, rapido
    3. Gemini Flash - Backup
    """

    @staticmethod
    def create_with_fallback(
        primary: str = "ollama",
        fallbacks: List[str] = ["mistral", "gemini"]
    ) -> "FallbackLLMProvider":
        providers = []

        if primary == "ollama":
            providers.append(OllamaProvider(model="phi3"))
        elif primary == "mistral":
            providers.append(MistralProvider(model="mistral-small-latest"))

        for fallback in fallbacks:
            if fallback == "mistral":
                providers.append(MistralProvider(model="mistral-small-latest"))
            elif fallback == "gemini":
                providers.append(GeminiProvider(model="gemini-1.5-flash"))

        return FallbackLLMProvider(providers)


class FallbackLLMProvider:
    """
    Proveedor con fallback automatico.

    Si el proveedor principal falla (timeout, rate limit, error),
    intenta con el siguiente en la cadena.
    """

    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers

    async def generate(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        last_error = None

        for provider in self.providers:
            try:
                return await provider.generate(messages, **kwargs)
            except (TimeoutError, RateLimitError) as e:
                last_error = e
                logger.warning(
                    "LLM provider failed, trying fallback",
                    provider=provider.__class__.__name__,
                    error=str(e)
                )
                continue

        # Todos los proveedores fallaron
        raise LLMUnavailableError(
            "All LLM providers failed",
            last_error=last_error
        )
```

### 5.5 Comparativa de Modelos Recomendados

| Modelo | Proveedor | Costo Input | Costo Output | Velocidad | Calidad |
|--------|-----------|-------------|--------------|-----------|---------|
| **phi3** | Ollama (local) | $0 | $0 | ~30 tok/s | Buena |
| **mistral-small-latest** | Mistral API | $0.1/1M | $0.3/1M | ~100 tok/s | Muy buena |
| **gemini-1.5-flash** | Google API | $0.075/1M | $0.30/1M | ~150 tok/s | Muy buena |
| **gpt-3.5-turbo** | OpenAI | $0.5/1M | $1.5/1M | ~80 tok/s | Buena |

**Recomendacion**: Mistral Small como principal para el Tutor, phi3 para operaciones locales (Gatekeeper, Safety, Scaffolding basico).

---

## 6. Infraestructura de Cache y Mensajeria

### 6.1 Redis: Optimizacion del Uso Actual

El proyecto ya utiliza Redis para cache de LLM y rate limiting. Para la arquitectura multi-agente, se propone extender su uso:

**Uso Actual**:
- Cache de respuestas LLM (TTL: 1 hora)
- Rate limiting por usuario

**Uso Propuesto Adicional**:
- Cache de embeddings frecuentes
- Cache de resultados RAG
- Cola de procesamiento para trazas N4
- Sesiones de agentes (estado temporal)

### 6.2 Estructura de Cache Propuesta

```python
# backend/core/cache.py (extension propuesta)
class AgentCacheManager:
    """
    Gestor de cache para la arquitectura multi-agente.

    Claves de cache:
    - rag:{query_hash} -> Resultados de busqueda vectorial (TTL: 30min)
    - emb:{text_hash} -> Embeddings de texto (TTL: 24h)
    - gk:{session}:{prompt_hash} -> Decisiones del Gatekeeper (TTL: 5min)
    - scaffold:{student}:{activity} -> Estado de andamiaje (TTL: sesion)
    """

    # TTLs por tipo de cache
    TTLS = {
        "rag": 1800,        # 30 minutos
        "embedding": 86400,  # 24 horas
        "gatekeeper": 300,   # 5 minutos
        "scaffold": 7200,    # 2 horas
    }

    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def get_rag_results(
        self,
        query: str,
        filters: Dict
    ) -> Optional[List[Dict]]:
        """Recupera resultados RAG cacheados."""
        key = self._make_key("rag", query, filters)
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_rag_results(
        self,
        query: str,
        filters: Dict,
        results: List[Dict]
    ):
        """Cachea resultados RAG."""
        key = self._make_key("rag", query, filters)
        await self.redis.setex(
            key,
            self.TTLS["rag"],
            json.dumps(results)
        )

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Recupera embedding cacheado."""
        key = f"emb:{self._hash(text)}"
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_embedding(self, text: str, embedding: List[float]):
        """Cachea embedding."""
        key = f"emb:{self._hash(text)}"
        await self.redis.setex(
            key,
            self.TTLS["embedding"],
            json.dumps(embedding)
        )
```

### 6.3 Estimacion de Memoria Redis

| Componente | Items Estimados | Tamano por Item | Total |
|------------|-----------------|-----------------|-------|
| Cache LLM existente | 1,000 | ~2 KB | ~2 MB |
| Cache RAG | 500 | ~5 KB | ~2.5 MB |
| Cache embeddings | 2,000 | ~1.5 KB | ~3 MB |
| Estado scaffolding | 100 | ~1 KB | ~0.1 MB |
| **Total** | | | **~8 MB** |

El limite actual de Redis (256 MB) es mas que suficiente.

---

## 7. Observabilidad y Monitoreo

### 7.1 Extension de Metricas Prometheus

La infraestructura de monitoreo existente (Prometheus + Grafana) debe extenderse para los nuevos agentes:

```python
# backend/api/monitoring/metrics.py (extension propuesta)

# === Metricas del Gatekeeper ===
gatekeeper_decisions = Counter(
    "gatekeeper_routing_decisions_total",
    "Decisiones de ruteo del Gatekeeper Cognitivo",
    ["decision", "risk_level"]
)

gatekeeper_latency = Histogram(
    "gatekeeper_processing_seconds",
    "Latencia del procesamiento del Gatekeeper",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# === Metricas de RAG ===
rag_queries = Counter(
    "rag_queries_total",
    "Total de consultas al sistema RAG",
    ["sufficient"]  # true/false
)

rag_confidence = Histogram(
    "rag_confidence_score",
    "Distribucion de scores de confianza RAG",
    buckets=[0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

rag_latency = Histogram(
    "rag_query_seconds",
    "Latencia de busqueda RAG",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5]
)

# === Metricas de Scaffolding ===
scaffolding_levels = Counter(
    "scaffolding_help_levels_total",
    "Niveles de ayuda aplicados",
    ["level"]  # 1, 2, 3, 4
)

scaffolding_progressions = Counter(
    "scaffolding_level_progressions_total",
    "Progresiones de nivel de ayuda (estudiante estancado)"
)

# === Metricas de Embeddings ===
embedding_latency = Histogram(
    "embedding_generation_seconds",
    "Latencia de generacion de embeddings",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25]
)

embedding_cache_hits = Counter(
    "embedding_cache_hits_total",
    "Cache hits de embeddings"
)
```

### 7.2 Dashboard Grafana para Agentes

Se propone crear un nuevo dashboard "Active-IA Agents" con los siguientes paneles:

1. **Gatekeeper Overview**
   - Tasa de decisiones por tipo (TUTOR, BLOCK, ESCALATE, FALLBACK)
   - Distribucion de niveles de riesgo
   - Latencia P50/P95/P99

2. **RAG Performance**
   - Consultas por minuto
   - Tasa de suficiencia (confidence >= threshold)
   - Latencia de busqueda
   - Cache hit rate

3. **Scaffolding Analytics**
   - Distribucion de niveles de ayuda
   - Tasa de progresion (estudiantes que avanzan de nivel)
   - Tiempo promedio por nivel

4. **LLM Costs** (nuevo)
   - Tokens consumidos por agente
   - Costo estimado diario/mensual
   - Tasa de fallback entre proveedores

---

## 8. Seguridad y Cumplimiento

### 8.1 Aislamiento de Datos en RAG

El Knowledge-Retrieval Agent solo debe acceder a contenido academico, nunca a datos personales de estudiantes. Se implementan las siguientes salvaguardas:

```python
# backend/core/knowledge_rag.py
class KnowledgeRetrievalAgent:
    """
    Agente de recuperacion con aislamiento de datos.

    REGLA DE SEGURIDAD: Esta clase SOLO accede a la tabla
    knowledge_documents, que contiene exclusivamente contenido
    academico. Nunca accede a users, sessions, traces, etc.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        # Verificar aislamiento al inicializar
        self._verify_isolation()

    def _verify_isolation(self):
        """
        Verifica que el repositorio solo tenga acceso a
        tablas de conocimiento, no a datos de estudiantes.
        """
        # La query solo puede tocar knowledge_documents
        allowed_tables = {"knowledge_documents"}

        # Implementar via SQLAlchemy event listeners
        # que bloqueen acceso a otras tablas

    async def retrieve(self, query: KnowledgeQuery) -> KnowledgeResult:
        # Query SOLO a knowledge_documents
        stmt = (
            select(KnowledgeDocument)
            .filter(KnowledgeDocument.unit == query.filters.unit)
            .order_by(
                KnowledgeDocument.embedding.cosine_distance(query.embedding)
            )
            .limit(query.max_results)
        )
        # ...
```

### 8.2 Sanitizacion de Prompts

El Gatekeeper debe sanitizar prompts antes de enviar a cualquier LLM:

```python
# backend/core/cognitive_gatekeeper.py
class PromptSanitizer:
    """
    Sanitizador de prompts para seguridad.

    Detecta y neutraliza:
    - Prompt injection
    - PII (datos personales)
    - Contenido inapropiado
    """

    INJECTION_PATTERNS = [
        r"ignor[ae]?\s+(las|todas|cualquier).*(reglas?|instrucciones?)",
        r"olvid[ae]?\s+(lo|todo).*(anterior|previo)",
        r"ahora\s+sos\s+un",
        r"nuevo\s+rol:",
        r"system\s*prompt",
    ]

    PII_PATTERNS = [
        r"\b\d{8}[a-zA-Z]\b",  # DNI
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b\d{9,}\b",  # Telefono
    ]

    def sanitize(self, prompt: str) -> Tuple[str, List[str]]:
        """
        Sanitiza el prompt y retorna (prompt_limpio, warnings).
        """
        warnings = []
        sanitized = prompt

        # Detectar injection
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, prompt, re.IGNORECASE):
                warnings.append(f"Possible injection detected: {pattern}")
                sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)

        # Redactar PII
        for pattern in self.PII_PATTERNS:
            if re.search(pattern, prompt):
                warnings.append("PII detected and redacted")
                sanitized = re.sub(pattern, "[PII]", sanitized)

        return sanitized, warnings
```

### 8.3 Logs de Auditoria

Todas las decisiones de agentes deben ser auditables:

```python
# backend/core/audit.py
class AgentAuditLogger:
    """
    Logger de auditoria para decisiones de agentes.

    Registra:
    - Quien (estudiante)
    - Que (decision del agente)
    - Por que (justificacion)
    - Cuando (timestamp)
    """

    async def log_gatekeeper_decision(
        self,
        session_id: str,
        student_id: str,
        original_prompt: str,
        sanitized_prompt: str,
        decision: GatekeeperOutput
    ):
        await self._log(
            agent="gatekeeper",
            session_id=session_id,
            student_id=student_id,
            action=decision.routing_decision.value,
            context={
                "cognitive_intent": decision.cognitive_intent.value,
                "risk_level": decision.risk_level.value,
                "delegation_signals": decision.delegation_signals,
                "prompt_modified": original_prompt != sanitized_prompt,
            }
        )
```

---

## 9. Estimacion de Costos

### 9.1 Escenario Base: Fase de Tesis

**Supuestos**:
- 1 desarrollador (investigador doctoral)
- 5-10 estudiantes de prueba piloto
- 4 semanas de evaluacion
- Servidor local (laptop/desktop)

| Componente | Descripcion | Costo Mensual |
|------------|-------------|---------------|
| PostgreSQL + pgvector | Self-hosted (Docker) | $0 |
| Redis | Self-hosted (Docker) | $0 |
| Ollama + phi3 | Self-hosted | $0 |
| Ollama + nomic-embed-text | Self-hosted | $0 |
| Mistral Small API | ~50,000 tokens/dia | ~$5 |
| Electricidad extra | GPU/CPU adicional | ~$5 |
| **Total** | | **~$10/mes** |

### 9.2 Escenario Piloto: Curso Universitario

**Supuestos**:
- 30 estudiantes
- 4 horas/semana de uso por estudiante
- 16 semanas (1 cuatrimestre)
- Servidor en la nube (VPS)

| Componente | Descripcion | Costo Mensual |
|------------|-------------|---------------|
| VPS (4 vCPU, 8GB RAM) | DigitalOcean/Hetzner | $40 |
| PostgreSQL + pgvector | En VPS | $0 (incluido) |
| Redis | En VPS | $0 (incluido) |
| Ollama + modelos | En VPS | $0 (incluido) |
| Mistral Small API | ~200,000 tokens/dia | ~$20 |
| Backups automaticos | Snapshots diarios | $5 |
| **Total** | | **~$65/mes** |

### 9.3 Escenario Produccion: Multi-Catedra

**Supuestos**:
- 200 estudiantes
- 5 catedras diferentes
- Alta disponibilidad requerida

| Componente | Descripcion | Costo Mensual |
|------------|-------------|---------------|
| Kubernetes cluster | 3 nodos, 4 vCPU cada uno | $150 |
| PostgreSQL gestionado | DigitalOcean Managed DB | $50 |
| Redis gestionado | DigitalOcean Managed Redis | $25 |
| Ollama (GPU node) | A10 GPU en cloud | $200 |
| Mistral API | ~1M tokens/dia | ~$100 |
| Monitoreo/Logging | Datadog o similar | $50 |
| **Total** | | **~$575/mes** |

### 9.4 Comparativa con Alternativas Cloud-First

Si se eligieran todas las opciones cloud en lugar de self-hosted:

| Componente | Opcion Self-Hosted | Opcion Cloud | Ahorro |
|------------|-------------------|--------------|--------|
| Vector DB | pgvector: $0 | Pinecone: $70 | $70/mes |
| Embeddings | Ollama: $0 | OpenAI: $20 | $20/mes |
| LLM | phi3 local: $0 | GPT-3.5 todo: $50 | $50/mes |
| **Total** | | | **$140/mes** |

El ahorro anual con la estrategia propuesta: **~$1,680/ano**

---

## 10. Arquitectura de Despliegue

### 10.1 Diagrama de Componentes

```
+------------------------------------------------------------------+
|                        INFRAESTRUCTURA                            |
+------------------------------------------------------------------+
|                                                                   |
|  +-------------------+     +-------------------+                  |
|  |    Frontend       |     |    Nginx          |                  |
|  |    (React 19)     |<--->|    Reverse Proxy  |                  |
|  |    Port: 3000     |     |    Port: 80/443   |                  |
|  +-------------------+     +-------------------+                  |
|                                     |                             |
|                                     v                             |
|  +----------------------------------------------------------+    |
|  |                    Backend (FastAPI)                      |    |
|  |                       Port: 8000                          |    |
|  +----------------------------------------------------------+    |
|  |                                                          |    |
|  |  +----------------+  +----------------+  +-------------+ |    |
|  |  |   AIGateway    |  |  Gatekeeper    |  | Knowledge   | |    |
|  |  |   (orquesta)   |  |  (clasifica)   |  | RAG         | |    |
|  |  +----------------+  +----------------+  +-------------+ |    |
|  |          |                   |                 |         |    |
|  |          v                   v                 v         |    |
|  |  +----------------+  +----------------+  +-------------+ |    |
|  |  |   T-IA-Cog     |  |  Fallback      |  | Scaffolding | |    |
|  |  |   (tutor)      |  |  Pedagogico    |  | Agent       | |    |
|  |  +----------------+  +----------------+  +-------------+ |    |
|  |                                                          |    |
|  +----------------------------------------------------------+    |
|            |              |              |                        |
|            v              v              v                        |
|  +-------------+  +-------------+  +------------------+          |
|  | PostgreSQL  |  |    Redis    |  |      Ollama      |          |
|  | + pgvector  |  |    Cache    |  | phi3 + nomic-emb |          |
|  | Port: 5432  |  |  Port: 6379 |  |   Port: 11434    |          |
|  +-------------+  +-------------+  +------------------+          |
|                                                                   |
+------------------------------------------------------------------+
|                    SERVICIOS EXTERNOS                             |
+------------------------------------------------------------------+
|                                                                   |
|  +-------------------+     +-------------------+                  |
|  |   Mistral API     |     |   Gemini API      |                  |
|  |   (LLM principal) |     |   (backup)        |                  |
|  +-------------------+     +-------------------+                  |
|                                                                   |
+------------------------------------------------------------------+
```

### 10.2 Docker Compose Actualizado

```yaml
# docker-compose.yml (adiciones propuestas)
services:
  # ... servicios existentes (api, postgres, redis, frontend) ...

  # ==========================================================================
  # Ollama - LLM Local + Embeddings
  # ==========================================================================
  ollama:
    image: ollama/ollama:latest
    container_name: ai-native-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_KEEP_ALIVE=24h
    networks:
      - ai-native-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
      interval: 30s
      timeout: 15s
      retries: 5
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
        reservations:
          memory: 4G

  # ==========================================================================
  # Ollama Model Loader (init container)
  # ==========================================================================
  ollama-init:
    image: curlimages/curl:latest
    container_name: ai-native-ollama-init
    depends_on:
      ollama:
        condition: service_healthy
    networks:
      - ai-native-network
    entrypoint: ["/bin/sh", "-c"]
    command:
      - |
        echo "Downloading phi3 model..."
        curl -X POST http://ollama:11434/api/pull -d '{"name": "phi3"}'
        echo "Downloading nomic-embed-text model..."
        curl -X POST http://ollama:11434/api/pull -d '{"name": "nomic-embed-text"}'
        echo "Models downloaded successfully"
    restart: "no"

# PostgreSQL debe incluir pgvector
  postgres:
    image: pgvector/pgvector:pg15  # Imagen con pgvector preinstalado
    # ... resto de configuracion igual ...
```

### 10.3 Migracion de Base de Datos

```sql
-- migrations/add_knowledge_documents.sql

-- Habilitar extension pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla de documentos de conocimiento
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    title VARCHAR(255),
    summary TEXT,
    content_type VARCHAR(50) NOT NULL,
    unit VARCHAR(100),
    topic VARCHAR(100),
    difficulty VARCHAR(20),
    language VARCHAR(10) DEFAULT 'es',
    embedding vector(384),
    source_id VARCHAR(255),
    source_file VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_knowledge_unit ON knowledge_documents(unit);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_documents(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_difficulty ON knowledge_documents(difficulty);
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata ON knowledge_documents USING gin(metadata);

-- Comentarios de documentacion
COMMENT ON TABLE knowledge_documents IS 'Documentos de conocimiento para RAG educativo';
COMMENT ON COLUMN knowledge_documents.embedding IS 'Vector de 384 dimensiones (nomic-embed-text)';
COMMENT ON COLUMN knowledge_documents.content_type IS 'Tipo: teoria, ejemplo, faq, consigna, ejercicio';
```

---

## 11. Plan de Implementacion

### 11.1 Fase 0: Preparacion de Infraestructura (1 semana)

**Objetivo**: Configurar los nuevos componentes sin afectar el sistema actual.

**Tareas**:
1. Actualizar imagen de PostgreSQL a `pgvector/pgvector:pg15`
2. Ejecutar migracion para crear tabla `knowledge_documents`
3. Agregar Ollama al docker-compose
4. Descargar modelos: `phi3` y `nomic-embed-text`
5. Verificar conectividad entre servicios

**Entregables**:
- [ ] pgvector funcionando
- [ ] Ollama respondiendo en `/api/embeddings`
- [ ] Tests de integracion pasando

### 11.2 Fase 1: Knowledge-Retrieval Agent (2 semanas)

**Objetivo**: Implementar el sistema RAG completo.

**Tareas**:
1. Implementar `OllamaEmbeddingProvider`
2. Implementar `KnowledgeRepository` con pgvector
3. Crear script de ingesta de documentos
4. Cargar corpus inicial (teoria, ejemplos, FAQ)
5. Implementar `KnowledgeRetrievalAgent`
6. Agregar cache de embeddings en Redis
7. Tests unitarios y de integracion

**Entregables**:
- [ ] Pipeline de ingesta funcionando
- [ ] Busqueda vectorial con filtros
- [ ] Cache de embeddings

### 11.3 Fase 2: Gatekeeper Cognitivo (2 semanas)

**Objetivo**: Implementar clasificacion y ruteo.

**Tareas**:
1. Implementar `CognitiveGatekeeper`
2. Integrar con `CognitiveReasoningEngine` existente
3. Implementar `PromptSanitizer`
4. Definir reglas de ruteo
5. Agregar metricas Prometheus
6. Feature flag `ENABLE_COGNITIVE_GATEKEEPER`

**Entregables**:
- [ ] Gatekeeper clasificando intenciones
- [ ] Sanitizacion de prompts
- [ ] Metricas de decisiones

### 11.4 Fase 3: Fallback y Scaffolding (2 semanas)

**Objetivo**: Completar agentes restantes.

**Tareas**:
1. Implementar `FallbackPedagogicoAgent`
2. Implementar `ScaffoldingAgent`
3. Integrar en flujo de AIGateway
4. Configurar phi3 local para estos agentes
5. Tests de flujo completo

**Entregables**:
- [ ] Fallback generando respuestas desacopladas
- [ ] Scaffolding ajustando niveles de ayuda
- [ ] Flujo end-to-end funcionando

### 11.5 Fase 4: Observabilidad y Tuning (1 semana)

**Objetivo**: Monitoreo y optimizacion.

**Tareas**:
1. Crear dashboard Grafana "Active-IA Agents"
2. Configurar alertas para latencia y errores
3. Optimizar indices de pgvector
4. Ajustar umbrales de confianza RAG
5. Documentar configuracion final

**Entregables**:
- [ ] Dashboard de agentes
- [ ] Alertas configuradas
- [ ] Documentacion completa

---

## 12. Alternativas Evaluadas

### 12.1 Bases de Datos Vectoriales Descartadas

| Solucion | Razon de Descarte |
|----------|-------------------|
| **Pinecone** | Costo ($70/mes minimo), vendor lock-in, datos en cloud externo |
| **Weaviate Cloud** | Costo ($25/mes minimo), complejidad innecesaria para el volumen |
| **Milvus** | Overhead operativo alto para un proyecto academico |
| **ChromaDB** | Buena opcion, pero agrega otro servicio cuando pgvector es suficiente |
| **Qdrant** | Similar a ChromaDB, preferimos consolidar en PostgreSQL |
| **FAISS** | Sin persistencia nativa, requiere implementacion adicional |

### 12.2 Modelos de Embeddings Descartados

| Modelo | Razon de Descarte |
|--------|-------------------|
| **OpenAI text-embedding-3** | Costo ($0.02-0.13/1M tokens), dependencia externa |
| **Cohere embed-v3** | Costo similar a OpenAI |
| **Voyage-2** | Mejor calidad pero costo prohibitivo para tesis |
| **all-MiniLM-L6-v2** | Menor calidad que nomic-embed-text |
| **instructor-xl** | Muy grande (5GB), lento sin GPU |

### 12.3 Proveedores LLM Descartados como Principales

| Proveedor | Razon de Descarte |
|-----------|-------------------|
| **OpenAI GPT-4** | Costo prohibitivo (~$30/1M tokens input) |
| **Anthropic Claude** | Costo alto (~$15/1M tokens) |
| **OpenAI GPT-3.5** | Funciona, pero Mistral Small es mas economico y comparable |
| **Llama 2 (local)** | Mas lento que phi3 para tareas simples |

---

## Conclusion

Esta propuesta de stack tecnologico logra implementar la arquitectura multi-agente Active-IA con un costo operativo de aproximadamente **$5-20 mensuales** durante la fase de tesis, escalando a **$65-100 mensuales** para un curso universitario completo.

Las decisiones clave son:

1. **pgvector sobre bases vectoriales especializadas**: Elimina complejidad operativa y costo, aprovechando la infraestructura PostgreSQL existente.

2. **Ollama para embeddings y LLM local**: Costo cero para operaciones de alta frecuencia (Gatekeeper, Scaffolding, Fallback).

3. **Mistral Small para el Tutor**: Balance optimo entre calidad pedagogica y costo (~$0.2/1M tokens).

4. **Fallback en cadena**: Resiliencia ante fallos sin duplicar infraestructura.

5. **Observabilidad integrada**: Reusa Prometheus/Grafana existentes.

El resultado es un sistema que cumple los requisitos pedagogicos de la tesis doctoral sin generar costos que excedan un presupuesto academico tipico, mientras mantiene la flexibilidad para escalar si el proyecto evoluciona a produccion institucional.

---

*Documento generado: Enero 2026*
*Version: 1.0*
*Autor: Propuesta tecnica basada en analisis de ImplementacionAgentes.md y stack actual*
