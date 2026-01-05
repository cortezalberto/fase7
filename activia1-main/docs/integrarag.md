# Integración de RAG al Sistema de Agentes AI-Native

**Versión**: 1.0
**Fecha**: Enero 2026
**Autor**: Cortez87
**Estado**: Propuesta de Implementación

---

## 1. Resumen Ejecutivo

### 1.1 Introducción y Contexto

La arquitectura actual del sistema AI-Native cuenta con seis agentes especializados que operan de manera coordinada para facilitar el proceso de enseñanza-aprendizaje de programación. Estos agentes —el Tutor Cognitivo (T-IA-Cog), el Evaluador de Procesos (E-IA-Proc), los Simuladores Profesionales (S-IA-X), el Analista de Riesgos (AR-IA), el Agente de Gobernanza (GOV-IA) y el Trazador de Nivel N4 (TC-N4)— han demostrado ser efectivos en sus respectivas funciones. Sin embargo, existe una oportunidad significativa de mejora: dotar a estos agentes de acceso a conocimiento contextualizado que enriquezca sus respuestas.

Retrieval-Augmented Generation, conocido como RAG, representa una técnica que combina la capacidad generativa de los modelos de lenguaje con la precisión de la recuperación de información documental. En lugar de depender únicamente del conocimiento embebido en los parámetros del modelo durante su entrenamiento, RAG permite consultar una base de conocimiento estructurada en tiempo real, recuperando fragmentos específicos de documentación que resultan relevantes para cada consulta particular del estudiante.

Este documento presenta una propuesta detallada para integrar RAG al ecosistema existente de agentes. La característica fundamental de esta integración es su naturaleza **aditiva y no disruptiva**: los agentes actuales continuarán funcionando exactamente como lo hacen ahora, mientras que RAG se incorporará como una capa opcional de enriquecimiento de contexto que puede activarse o desactivarse mediante configuración, sin necesidad de modificar el código desplegado.

### 1.2 Objetivo Principal

El objetivo central de esta integración consiste en complementar las respuestas generadas por los agentes —especialmente T-IA-Cog y S-IA-X— con conocimiento contextual recuperado dinámicamente de fuentes académicas autorizadas. Este conocimiento incluirá material de cátedra como teoría, ejemplos resueltos y ejercicios propuestos; documentación técnica relevante a los temas tratados; preguntas frecuentes que han surgido históricamente en el contexto de la materia; y las consignas específicas de las actividades que los estudiantes deben realizar.

Al proporcionar este contexto adicional, los agentes podrán ofrecer respuestas más precisas y alineadas con el contenido específico de cada asignatura, manteniendo siempre la coherencia pedagógica que caracteriza al sistema actual.

### 1.3 El Principio de Integración: Antes, No Dentro

Para comprender cómo RAG se incorpora sin alterar la lógica existente, es esencial entender el flujo de procesamiento actual y cómo se modificará:

**Flujo actual (sin RAG):**
```
Estudiante -> AIGateway -> CRPE -> T-IA-Cog -> LLM -> Respuesta
```

**Flujo propuesto (con RAG):**
```
Estudiante -> AIGateway -> CRPE -> [Knowledge-RAG] -> T-IA-Cog -> LLM -> Respuesta
                                          |
                                          v
                                    pgvector (embeddings)
```

La diferencia fundamental radica en la inserción del componente Knowledge-RAG **antes** del agente destino. Este componente actúa como un intermediario que enriquece el prompt con contexto relevante antes de que llegue al agente. El agente, por tanto, recibe información adicional que le permite generar respuestas más fundamentadas, pero su lógica interna —sus modos de operación, sus reglas pedagógicas, sus mecanismos de semáforo— permanece completamente intacta. El agente simplemente trabaja con un prompt más rico en información, pero no necesita saber que esa información proviene de un sistema RAG; para él, es simplemente parte del contexto de entrada.

---

## 2. Arquitectura de Integración

### 2.1 Nuevos Componentes del Sistema

La implementación de RAG requiere la introducción de cuatro nuevos componentes que se integrarán armoniosamente con la arquitectura existente. Cada uno de estos componentes tiene una responsabilidad claramente definida, siguiendo los principios de diseño que ya caracterizan al sistema.

El **EmbeddingProvider** constituye el corazón del sistema de vectorización. Este componente se encarga de transformar textos —ya sean consultas de estudiantes o contenido documental— en representaciones vectoriales de 384 dimensiones utilizando el modelo nomic-embed-text a través de Ollama. La elección de este modelo responde a criterios tanto técnicos como económicos: ofrece embeddings de alta calidad para texto en español, opera de manera completamente local eliminando costos de API externos, y su dimensionalidad de 384 proporciona un balance óptimo entre expresividad semántica y eficiencia de almacenamiento.

El **KnowledgeRepository** extiende el patrón de repositorio que ya utiliza el sistema para otras entidades del dominio. Este repositorio gestiona el ciclo de vida completo de los documentos de conocimiento: creación, lectura, actualización y eliminación lógica. Su característica distintiva es la capacidad de realizar búsquedas por similitud vectorial, permitiendo encontrar documentos semánticamente relacionados con una consulta aunque no compartan palabras exactas. Por ejemplo, una pregunta sobre "cómo funciona el algoritmo de ordenamiento rápido" recuperará correctamente documentos que hablen de "quicksort" aunque esa palabra específica no aparezca en la consulta.

El **KnowledgeRAGAgent** representa el nuevo agente que orquesta el proceso completo de recuperación de conocimiento. A diferencia de los otros agentes del sistema que generan contenido, este agente tiene una función exclusivamente de intermediación: recibe la consulta del estudiante, la transforma en un embedding, busca documentos relevantes en la base de conocimiento, evalúa la calidad del contexto recuperado, y construye un texto enriquecido que será prepuesto al prompt original. Este agente implementa lógica sofisticada para determinar cuándo el contexto recuperado es suficientemente relevante como para incluirlo, evitando así contaminar el prompt con información tangencial que podría confundir al agente destino.

Finalmente, el **KnowledgeDocument** constituye el modelo ORM que representa un documento de conocimiento en la base de datos. Cada documento almacena no solo su contenido textual, sino también metadatos ricos que facilitan el filtrado: tipo de contenido (teoría, ejemplo, pregunta frecuente, consigna), unidad temática a la que pertenece, nivel de dificultad, código de materia, y por supuesto, su representación vectorial que permite la búsqueda semántica.

La siguiente tabla resume la ubicación y responsabilidad de cada componente:

| Componente | Archivo | Responsabilidad |
|------------|---------|-----------------|
| `EmbeddingProvider` | `backend/core/embeddings.py` | Genera vectores de 384 dimensiones usando Ollama + nomic-embed-text |
| `KnowledgeRepository` | `backend/database/repositories/knowledge_repository.py` | CRUD de documentos + búsqueda vectorial en pgvector |
| `KnowledgeRAGAgent` | `backend/agents/knowledge_rag.py` | Orquesta búsqueda y construcción de contexto enriquecido |
| `KnowledgeDocument` | `backend/database/models/knowledge.py` | Modelo ORM para documentos con embedding |

### 2.2 Flujo de Datos Detallado: Un Ejemplo Concreto

Para ilustrar cómo estos componentes trabajan coordinadamente, consideremos un escenario realista donde un estudiante interactúa con el sistema mientras trabaja en la unidad de algoritmos de ordenamiento.

**Paso 1: Recepción de la Consulta**

El estudiante escribe en el chat: "No entiendo cómo funciona quicksort". Esta consulta llega al AIGateway, que como siempre actúa como punto de entrada centralizado para todas las interacciones del sistema.

**Paso 2: Análisis Cognitivo por CRPE**

El Cognitive Recognition and Processing Engine (CRPE) analiza la intención cognitiva del mensaje. Basándose en patrones lingüísticos como "no entiendo" y la naturaleza conceptual de la pregunta, clasifica el estado cognitivo del estudiante como EXPLORACIÓN. Esta clasificación influirá tanto en el modo que adoptará el Tutor como en los tipos de documentos que RAG priorizará en su búsqueda.

**Paso 3: Recuperación de Conocimiento por RAG**

Aquí interviene el nuevo componente. El KnowledgeRAGAgent recibe la consulta y ejecuta un proceso de tres etapas:

Primero, genera un embedding de la consulta invocando al EmbeddingProvider. El texto "No entiendo cómo funciona quicksort" se transforma en un vector de 384 números reales que captura su significado semántico. Este vector tiene la propiedad de que estará "cerca" de otros vectores que representen conceptos relacionados, incluso si utilizan vocabulario diferente.

Segundo, busca en pgvector documentos cuyas representaciones vectoriales sean similares al vector de la consulta. La búsqueda aplica filtros contextuales: dado que el estudiante está en la unidad de "algoritmos_ordenamiento" (información disponible en el contexto de sesión), se priorizan documentos de esa unidad. La búsqueda utiliza distancia coseno para medir similitud, retornando los tres documentos más relevantes que superen un umbral mínimo de confianza.

Tercero, evalúa la calidad del contexto recuperado. Si el documento más similar tiene un score de 0.85 y los otros dos tienen 0.78 y 0.72, el sistema determina que la confianza es ALTA y que el contexto es suficiente para enriquecer el prompt.

**Paso 4: Construcción del Prompt Enriquecido**

El AIGateway recibe el resultado de RAG y construye un nuevo prompt que combina el contexto recuperado con la pregunta original:

```
[CONTEXTO PEDAGÓGICO]
- Quicksort es un algoritmo de ordenamiento basado en la estrategia divide y vencerás...
- Su complejidad promedio es O(n log n), aunque el peor caso es O(n²)...
- Ejemplo en Python: def quicksort(arr): if len(arr) <= 1: return arr...

[PREGUNTA DEL ESTUDIANTE]
No entiendo cómo funciona quicksort
```

**Paso 5: Procesamiento por el Agente (Sin Cambios)**

T-IA-Cog recibe este prompt enriquecido. Desde su perspectiva, simplemente tiene más información de contexto con la cual trabajar. Su lógica interna opera exactamente como siempre: evalúa el estado cognitivo del estudiante, selecciona el modo pedagógico apropiado (posiblemente socrático dado que el estudiante está explorando), y genera una respuesta que guía sin revelar directamente la solución.

**Paso 6: Respuesta al Estudiante**

El LLM, guiado por las reglas pedagógicas del Tutor y enriquecido con el contexto de RAG, genera una respuesta que probablemente comenzará con preguntas guía: "Cuando tienes una lista desordenada, ¿qué crees que pasaría si eligieras un elemento como 'pivote' y separaras los demás según sean mayores o menores que él?"

### 2.3 Puntos de Integración en el Código Existente

La belleza de esta arquitectura radica en lo mínimamente invasiva que resulta su integración. El único componente existente que requiere modificación es el AIGateway, y los cambios son puramente aditivos.

La modificación consiste en agregar un parámetro opcional al constructor del AIGateway que permite inyectar una instancia del KnowledgeRAGAgent. Cuando este parámetro está presente y la característica está habilitada, el gateway consulta al agente RAG antes de pasar el prompt al motor cognitivo. Si RAG no está configurado o retorna un resultado de baja confianza, el flujo continúa exactamente como antes.

```python
# backend/core/ai_gateway.py

class AIGateway:
    def __init__(
        self,
        # ... parámetros existentes ...
        knowledge_rag: Optional["KnowledgeRAGAgent"] = None,  # NUEVO
    ):
        # ... inicialización existente ...
        self.knowledge_rag = knowledge_rag  # NUEVO

    async def process_interaction(
        self,
        session_id: str,
        prompt: str,
        # ... otros parámetros ...
    ) -> Dict[str, Any]:
        # ... código existente de CRPE ...

        # === NUEVO: Enriquecer con RAG si está disponible ===
        enriched_prompt = prompt
        rag_context = None

        if self.knowledge_rag:
            rag_result = await self.knowledge_rag.retrieve(
                query=prompt,
                filters={
                    "unit": session_context.get("current_unit"),
                    "difficulty": student_profile.get("level"),
                }
            )
            if rag_result.is_sufficient:
                enriched_prompt = self._build_enriched_prompt(
                    original=prompt,
                    context=rag_result.documents
                )
                rag_context = rag_result

        # === Continuar flujo normal con prompt enriquecido ===
        response = await self.cognitive_engine.process(
            prompt=enriched_prompt,  # Ahora potencialmente enriquecido
            mode=agent_mode,
            # ... resto igual ...
        )

        return response
```

Esta estructura garantiza que si `knowledge_rag` es `None` o si el resultado no alcanza el umbral de confianza, el sistema se comporta exactamente como lo hacía antes de la integración. El principio de fallo seguro está incorporado en el diseño mismo.

### 2.4 Feature Flags para Despliegue Gradual

Una característica crítica de esta propuesta es la capacidad de controlar la activación de RAG mediante variables de entorno, sin necesidad de modificar código ni redesplegar la aplicación.

```python
# backend/api/config.py

# Feature flags para RAG
RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_MIN_CONFIDENCE = float(os.getenv("RAG_MIN_CONFIDENCE", "0.7"))
RAG_MAX_DOCUMENTS = int(os.getenv("RAG_MAX_DOCUMENTS", "3"))
```

Estas variables permiten tres niveles de control:

`RAG_ENABLED` actúa como interruptor principal. Con valor `false`, el sistema ignora completamente el componente RAG aunque esté configurado. Esto permite desactivar la funcionalidad instantáneamente si se detecta algún problema en producción.

`RAG_MIN_CONFIDENCE` controla el umbral de calidad que debe alcanzar el contexto recuperado para ser incluido en el prompt. Un valor de 0.7 significa que solo se usará contexto cuando al menos uno de los documentos tenga una similitud coseno de 0.7 o superior con la consulta. Ajustar este valor permite balancear entre cobertura (valores más bajos incluyen más contexto) y precisión (valores más altos aseguran mayor relevancia).

`RAG_MAX_DOCUMENTS` limita la cantidad de documentos que se incluirán en el contexto. Más documentos proporcionan más información pero también incrementan el tamaño del prompt y el costo de tokens del LLM. El valor por defecto de 3 representa un balance razonable.

El despliegue gradual podría seguir esta secuencia:

```bash
# Semana 1: Activar solo en desarrollo
RAG_ENABLED=true python -m backend  # Solo ambiente local

# Semana 2: Activar en staging con umbral alto
RAG_ENABLED=true RAG_MIN_CONFIDENCE=0.85 ...  # Solo contexto muy relevante

# Semana 3: Producción con umbral moderado
RAG_ENABLED=true RAG_MIN_CONFIDENCE=0.7 ...

# Si hay problemas: desactivar inmediatamente
RAG_ENABLED=false python -m backend  # Volver al comportamiento original
```

---

## 3. Modelo de Datos

### 3.1 Diseño de la Tabla de Documentos

El almacenamiento de documentos de conocimiento requiere una estructura que soporte tanto las operaciones tradicionales de base de datos (filtrado, ordenamiento, paginación) como la búsqueda vectorial por similitud semántica. PostgreSQL, con la extensión pgvector, proporciona esta capacidad dual en una única base de datos, evitando la complejidad de mantener sistemas separados sincronizados.

La tabla `knowledge_documents` ha sido diseñada contemplando los diversos tipos de contenido académico que el sistema necesitará almacenar y las múltiples dimensiones por las cuales ese contenido puede ser filtrado.

```sql
-- Migración: backend/database/migrations/add_knowledge_rag.py

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    -- Identificación única
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Contenido principal
    content TEXT NOT NULL,
    title VARCHAR(255),
    summary TEXT,

    -- Clasificación pedagógica
    content_type VARCHAR(50) NOT NULL,  -- teoria, ejemplo, faq, consigna, ejercicio
    unit VARCHAR(100),                   -- unidad temática (ej: "algoritmos_ordenamiento")
    topic VARCHAR(100),                  -- tema específico (ej: "quicksort")
    difficulty VARCHAR(20),              -- basico, intermedio, avanzado
    language VARCHAR(10) DEFAULT 'es',

    -- Embedding vectorial (nomic-embed-text = 384 dimensiones)
    embedding vector(384),

    -- Trazabilidad y origen
    source_id VARCHAR(255),              -- ID del documento original
    source_file VARCHAR(500),            -- Ruta del archivo fuente
    materia_code VARCHAR(50),            -- FK lógica a materias
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete

    -- Metadatos extensibles
    metadata JSONB DEFAULT '{}'
);

-- Índice vectorial IVFFlat (óptimo para <1M vectores)
CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Índices para filtros frecuentes
CREATE INDEX IF NOT EXISTS idx_knowledge_unit ON knowledge_documents(unit);
CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_documents(content_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_materia ON knowledge_documents(materia_code);
CREATE INDEX IF NOT EXISTS idx_knowledge_deleted ON knowledge_documents(deleted_at);
```

Cada columna tiene un propósito específico que merece explicación:

El campo `content` almacena el texto completo del documento. No hay límite artificial en su longitud, permitiendo desde fragmentos breves de preguntas frecuentes hasta capítulos completos de teoría. Sin embargo, para la generación de embeddings solo se utilizarán los primeros 2000 caracteres, siguiendo las mejores prácticas para nomic-embed-text.

Los campos `title` y `summary` son opcionales pero altamente recomendados. El título facilita la identificación humana del documento en interfaces de administración, mientras que el resumen puede incluirse en el contexto cuando el contenido completo es demasiado extenso, proporcionando una versión condensada de la información.

El campo `content_type` clasifica la naturaleza del documento. Esta clasificación permite a RAG priorizar diferentes tipos según el contexto: cuando un estudiante está explorando un concepto nuevo, los documentos de tipo "teoria" tendrán mayor relevancia; cuando está depurando código, los "ejemplo" pueden ser más útiles.

Los campos `unit` y `topic` establecen la jerarquía temática. Una unidad como "algoritmos_ordenamiento" puede contener múltiples temas: "quicksort", "mergesort", "heapsort". Esta estructura permite filtrar por granularidades diferentes según el contexto de la sesión del estudiante.

El campo `difficulty` con valores "basico", "intermedio" o "avanzado" permite personalizar el nivel del contenido recuperado según el perfil del estudiante. Un estudiante con historial de buen rendimiento recibirá contexto más avanzado; uno que muestra señales de frustración recibirá explicaciones más fundamentales.

El campo `embedding` almacena el vector de 384 dimensiones que representa semánticamente el contenido del documento. Este vector es el que permite la búsqueda por similitud.

Los campos de trazabilidad (`source_id`, `source_file`, `materia_code`) mantienen la conexión con los documentos originales y la estructura académica, facilitando auditoría y actualizaciones cuando el material fuente cambia.

La columna `deleted_at` implementa el patrón de soft delete consistente con el resto del sistema, permitiendo "eliminar" documentos sin perderlos permanentemente.

Finalmente, `metadata` como JSONB proporciona flexibilidad para almacenar información adicional que pueda surgir sin requerir cambios de esquema: URLs de referencia, autores, versiones, etiquetas personalizadas.

El índice IVFFlat (Inverted File with Flat compression) es crucial para el rendimiento. Este tipo de índice divide el espacio vectorial en 100 listas (clusters) y durante la búsqueda solo explora las listas más prometedoras, reduciendo drásticamente el tiempo de búsqueda en comparación con un escaneo secuencial de todos los vectores. La configuración `WITH (lists = 100)` está optimizada para colecciones de hasta un millón de vectores; para colecciones mayores, podría ajustarse.

### 3.2 Modelo ORM

El modelo SQLAlchemy refleja la estructura de la tabla y proporciona la interfaz Python para manipular documentos. Utiliza la integración pgvector-sqlalchemy para el manejo nativo del tipo Vector.

```python
# backend/database/models/knowledge.py

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone
import uuid

from .base import Base

class KnowledgeDocumentDB(Base):
    """
    Documento de conocimiento para RAG educativo.

    Este modelo representa un fragmento de contenido académico
    que puede ser recuperado semánticamente para enriquecer
    las respuestas de los agentes del sistema.

    Atributos:
        id: Identificador único UUID.
        content: Texto completo del documento.
        title: Título descriptivo (opcional).
        summary: Resumen para contextos donde el contenido completo es muy largo.
        content_type: Clasificación del tipo de contenido (teoria, ejemplo, faq, etc.).
        unit: Unidad temática a la que pertenece.
        topic: Tema específico dentro de la unidad.
        difficulty: Nivel de dificultad (basico, intermedio, avanzado).
        language: Idioma del contenido (default: español).
        embedding: Vector de 384 dimensiones para búsqueda semántica.
        source_id: ID del documento fuente original.
        source_file: Ruta del archivo desde donde se importó.
        materia_code: Código de la materia asociada.
        metadata: Información adicional en formato JSON.
    """
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Contenido
    content = Column(Text, nullable=False)
    title = Column(String(255))
    summary = Column(Text)

    # Clasificación
    content_type = Column(String(50), nullable=False)
    unit = Column(String(100), index=True)
    topic = Column(String(100))
    difficulty = Column(String(20))
    language = Column(String(10), default="es")

    # Embedding
    embedding = Column(Vector(384))

    # Trazabilidad
    source_id = Column(String(255))
    source_file = Column(String(500))
    materia_code = Column(String(50), index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Metadatos
    metadata = Column(JSONB, default=dict)
```

---

## 4. Implementación de Componentes

### 4.1 EmbeddingProvider: El Corazón de la Vectorización

El EmbeddingProvider es responsable de la transformación fundamental que hace posible la búsqueda semántica: convertir texto legible por humanos en representaciones vectoriales que capturan significado.

La implementación utiliza Ollama como servidor de inferencia local, ejecutando el modelo nomic-embed-text. Esta elección tiene implicaciones importantes tanto técnicas como de costos:

Desde la perspectiva de costos, Ollama es completamente gratuito ya que ejecuta modelos localmente. No hay cargos por API como ocurriría con OpenAI Embeddings o servicios similares. Dado que el sistema generará embeddings para cada documento ingresado (potencialmente miles) y para cada consulta de estudiante (potencialmente decenas de miles por día), esta diferencia de costos es sustancial.

Desde la perspectiva técnica, nomic-embed-text produce vectores de 384 dimensiones que han demostrado excelente rendimiento en tareas de recuperación semántica para texto en español. Su latencia típica de 10-50 milisegundos por embedding es aceptable para un sistema interactivo.

El componente implementa también un sistema de caché a través de Redis para evitar regenerar embeddings de consultas repetidas. Dado que muchos estudiantes hacen preguntas similares ("no entiendo recursión", "cómo funciona un for"), el cache puede reducir significativamente la carga en Ollama.

```python
# backend/core/embeddings.py

import httpx
from typing import List, Optional
import asyncio
import hashlib
from ..core.cache import LLMResponseCache

class OllamaEmbeddingProvider:
    """
    Proveedor de embeddings usando Ollama + nomic-embed-text.

    Este componente transforma texto en representaciones vectoriales
    de 384 dimensiones que capturan el significado semántico del
    contenido, permitiendo búsquedas por similitud.

    La vectorización se realiza localmente a través de Ollama,
    eliminando costos de API externos y garantizando privacidad
    de los datos (ningún contenido sale del servidor).

    Características:
    - Costo: $0 (self-hosted)
    - Dimensiones: 384
    - Latencia: 10-50ms por documento
    - Cache integrado vía Redis para consultas repetidas
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "nomic-embed-text",
        timeout: float = 30.0,
        cache: Optional[LLMResponseCache] = None
    ):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.cache = cache
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP asíncrono."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client

    def _cache_key(self, text: str) -> str:
        """
        Genera una clave de cache única para un texto.

        Utiliza MD5 para producir una clave de longitud fija
        independientemente del tamaño del texto de entrada.
        """
        return f"emb:{hashlib.md5(text.encode()).hexdigest()}"

    async def embed(self, text: str) -> List[float]:
        """
        Genera el embedding vectorial para un texto.

        El proceso sigue estos pasos:
        1. Verifica si existe en cache (evita llamadas repetidas)
        2. Si no está en cache, invoca a Ollama
        3. Almacena el resultado en cache con TTL de 24 horas
        4. Retorna el vector de 384 dimensiones

        Args:
            text: Texto a vectorizar (máx. recomendado: 2000 caracteres)

        Returns:
            Lista de 384 números flotantes representando el embedding
        """
        # Verificar cache primero
        if self.cache:
            cache_key = self._cache_key(text)
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        # Generar embedding mediante Ollama
        client = await self._get_client()
        response = await client.post(
            "/api/embeddings",
            json={"model": self.model, "prompt": text}
        )
        response.raise_for_status()
        embedding = response.json()["embedding"]

        # Guardar en cache (TTL: 24 horas)
        if self.cache:
            await self.cache.set(cache_key, embedding, ttl=86400)

        return embedding

    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Genera embeddings para múltiples textos en lotes.

        Para evitar sobrecargar a Ollama con demasiadas
        solicitudes simultáneas, procesa los textos en
        lotes de tamaño configurable.

        Args:
            texts: Lista de textos a vectorizar
            batch_size: Cantidad de textos a procesar simultáneamente

        Returns:
            Lista de embeddings en el mismo orden que los textos de entrada
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
        """Cierra el cliente HTTP liberando recursos."""
        if self._client:
            await self._client.aclose()
            self._client = None
```

### 4.2 KnowledgeRepository: Gestión y Búsqueda de Documentos

El repositorio de conocimiento implementa las operaciones de persistencia y recuperación de documentos, con especial énfasis en la búsqueda por similitud vectorial. Extiende el patrón BaseRepository que ya utilizan otros repositorios del sistema, garantizando consistencia arquitectónica.

La operación más interesante es `search_similar`, que combina búsqueda vectorial con filtros tradicionales de SQL. Esta hibridación permite consultas como "encuentra documentos sobre quicksort, de tipo teoría, dificultad intermedia, que sean semánticamente similares a la pregunta del estudiante". La búsqueda vectorial identifica relevancia semántica mientras los filtros aseguran adecuación contextual.

```python
# backend/database/repositories/knowledge_repository.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from pgvector.sqlalchemy import Vector

from ..models.knowledge import KnowledgeDocumentDB
from .base import BaseRepository

class KnowledgeRepository(BaseRepository):
    """
    Repositorio para documentos de conocimiento con búsqueda vectorial.

    Combina operaciones CRUD tradicionales con búsqueda semántica
    por embeddings, permitiendo recuperar documentos relevantes
    basándose tanto en similitud de significado como en filtros
    estructurados (unidad, tipo, dificultad).

    La búsqueda vectorial utiliza distancia coseno, donde valores
    cercanos a 1 indican alta similitud y cercanos a 0 indican
    baja similitud. El umbral por defecto de 0.5 filtra documentos
    que comparten al menos cierta relación semántica con la consulta.
    """

    def __init__(self, db_session: Session):
        super().__init__(db_session)
        self.model = KnowledgeDocumentDB

    async def search_similar(
        self,
        query_embedding: List[float],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Busca documentos semánticamente similares a una consulta.

        El proceso de búsqueda opera en tres fases:
        1. Construcción de condiciones: combina filtros estructurados
           con exclusión de documentos soft-deleted
        2. Ejecución de query vectorial: utiliza índice IVFFlat para
           encontrar vectores cercanos eficientemente
        3. Post-filtrado por umbral: descarta resultados con similitud
           inferior al mínimo requerido

        Args:
            query_embedding: Vector de 384 dimensiones de la consulta
            filters: Diccionario opcional con filtros:
                - unit: Unidad temática
                - content_type: Tipo de contenido
                - difficulty: Nivel de dificultad
                - materia_code: Código de materia
            limit: Máximo número de resultados
            min_similarity: Umbral mínimo de similitud (0-1)

        Returns:
            Lista de documentos con su score de similitud, ordenados
            de mayor a menor relevancia
        """
        # Construir condiciones base
        conditions = [KnowledgeDocumentDB.deleted_at.is_(None)]

        # Agregar filtros opcionales
        if filters:
            if filters.get("unit"):
                conditions.append(KnowledgeDocumentDB.unit == filters["unit"])
            if filters.get("content_type"):
                conditions.append(KnowledgeDocumentDB.content_type == filters["content_type"])
            if filters.get("difficulty"):
                conditions.append(KnowledgeDocumentDB.difficulty == filters["difficulty"])
            if filters.get("materia_code"):
                conditions.append(KnowledgeDocumentDB.materia_code == filters["materia_code"])

        # Query con similitud coseno
        # La distancia coseno va de 0 (idénticos) a 2 (opuestos)
        # Convertimos a similitud: 1 - distancia/2, normalizando a 0-1
        stmt = (
            select(
                KnowledgeDocumentDB,
                (1 - KnowledgeDocumentDB.embedding.cosine_distance(query_embedding)).label("similarity")
            )
            .where(and_(*conditions))
            .order_by(KnowledgeDocumentDB.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        results = self.db.execute(stmt).all()

        # Filtrar por similitud mínima y formatear respuesta
        documents = []
        for doc, similarity in results:
            if similarity >= min_similarity:
                documents.append({
                    "id": str(doc.id),
                    "content": doc.content,
                    "title": doc.title,
                    "summary": doc.summary,
                    "content_type": doc.content_type,
                    "unit": doc.unit,
                    "topic": doc.topic,
                    "difficulty": doc.difficulty,
                    "similarity": float(similarity),
                    "metadata": doc.metadata or {}
                })

        return documents

    def create_with_embedding(
        self,
        content: str,
        embedding: List[float],
        **kwargs
    ) -> KnowledgeDocumentDB:
        """
        Crea un nuevo documento de conocimiento con su embedding.

        Este método es utilizado cuando se ingresa contenido
        individual, como cuando un docente agrega una nueva
        explicación o ejemplo.

        Args:
            content: Texto del documento
            embedding: Vector de 384 dimensiones
            **kwargs: Metadatos adicionales (title, unit, topic, etc.)

        Returns:
            Instancia del documento creado
        """
        doc = KnowledgeDocumentDB(
            content=content,
            embedding=embedding,
            **kwargs
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def bulk_create_with_embeddings(
        self,
        documents: List[Dict[str, Any]]
    ) -> int:
        """
        Crea múltiples documentos en una sola transacción.

        Optimizado para la carga inicial de corpus académicos
        donde pueden existir cientos o miles de documentos.
        Utiliza bulk_save_objects para minimizar roundtrips
        a la base de datos.

        Args:
            documents: Lista de diccionarios con content, embedding,
                      y metadatos de cada documento

        Returns:
            Cantidad de documentos insertados
        """
        db_docs = [
            KnowledgeDocumentDB(**doc)
            for doc in documents
        ]
        self.db.bulk_save_objects(db_docs)
        self.db.commit()
        return len(db_docs)
```

### 4.3 KnowledgeRAGAgent: El Orquestador de Recuperación

El agente RAG constituye el componente central que coordina todo el proceso de recuperación de conocimiento. A diferencia de los otros agentes del sistema (Tutor, Evaluador, Simuladores) que generan contenido, este agente tiene una función exclusivamente de intermediación: prepara el terreno para que otros agentes trabajen con información enriquecida.

La decisión arquitectónica de implementar RAG como un agente separado —en lugar de incorporarlo directamente en el AIGateway— responde a varios principios de diseño:

**Separación de responsabilidades**: El gateway orquesta el flujo general; el agente RAG se especializa en recuperación de conocimiento. Cada componente tiene una única responsabilidad bien definida.

**Reusabilidad**: El agente RAG puede ser utilizado por diferentes flujos sin duplicar lógica. Si en el futuro se quiere agregar recuperación de conocimiento al modo de evaluación, simplemente se conecta el mismo agente.

**Testabilidad**: Un agente independiente puede probarse unitariamente con facilidad, verificando su comportamiento ante diferentes consultas y configuraciones sin necesidad de levantar toda la infraestructura del gateway.

**Configurabilidad**: Los parámetros del agente (umbral de confianza, número máximo de documentos, plantilla de contexto) pueden ajustarse sin afectar otros componentes.

```python
# backend/agents/knowledge_rag.py

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.embeddings import OllamaEmbeddingProvider
from ..database.repositories.knowledge_repository import KnowledgeRepository

logger = logging.getLogger(__name__)

class RAGConfidence(str, Enum):
    """
    Niveles de confianza del resultado RAG.

    La confianza indica qué tan relevantes son los documentos
    recuperados para la consulta del estudiante.
    """
    HIGH = "high"       # >= 0.8: Documentos altamente relevantes
    MEDIUM = "medium"   # 0.6-0.8: Documentos relacionados
    LOW = "low"         # 0.4-0.6: Documentos tangencialmente relacionados
    NONE = "none"       # < 0.4: Sin contexto útil

@dataclass
class RAGResult:
    """
    Resultado completo de una consulta RAG.

    Encapsula tanto los documentos recuperados como metadatos
    sobre la calidad de la recuperación, permitiendo a los
    consumidores (como AIGateway) tomar decisiones informadas
    sobre si usar o descartar el contexto.
    """
    documents: List[Dict[str, Any]]
    confidence: RAGConfidence
    is_sufficient: bool
    context_text: str
    query_embedding: List[float]

    @property
    def avg_similarity(self) -> float:
        """Calcula la similitud promedio de los documentos recuperados."""
        if not self.documents:
            return 0.0
        return sum(d["similarity"] for d in self.documents) / len(self.documents)


class KnowledgeRAGAgent:
    """
    Agente de Recuperación de Conocimiento Aumentada por Generación.

    Este agente actúa como intermediario entre las consultas de los
    estudiantes y los agentes generativos del sistema. Su función es
    enriquecer el contexto disponible para esos agentes recuperando
    información relevante de la base de conocimiento.

    El agente NO genera respuestas directamente. Solo recupera y
    organiza contexto para que otros agentes (especialmente T-IA-Cog)
    lo utilicen en su generación.

    Flujo de operación:
    1. Recibir consulta del estudiante
    2. Generar embedding de la consulta
    3. Buscar documentos similares en pgvector
    4. Evaluar si el contexto recuperado es suficientemente relevante
    5. Construir texto de contexto formateado para el agente destino

    Umbrales de confianza:
    - HIGH (>= 0.8): Documentos muy relevantes, usar siempre
    - MEDIUM (0.6-0.8): Documentos útiles, usar si hay al menos 2
    - LOW (0.4-0.6): Documentos tangenciales, probablemente omitir
    - NONE (< 0.4): Sin contexto útil, continuar sin enriquecer
    """

    # Umbrales de confianza
    CONFIDENCE_HIGH = 0.8
    CONFIDENCE_MEDIUM = 0.6
    CONFIDENCE_LOW = 0.4

    def __init__(
        self,
        embedding_provider: OllamaEmbeddingProvider,
        knowledge_repo: KnowledgeRepository,
        config: Optional[Dict[str, Any]] = None
    ):
        self.embeddings = embedding_provider
        self.knowledge_repo = knowledge_repo
        self.config = config or {}

        # Configuración con valores por defecto
        self.max_documents = self.config.get("max_documents", 3)
        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.context_template = self.config.get("context_template", self._default_template())

    def _default_template(self) -> str:
        """
        Plantilla por defecto para el contexto inyectado.

        Esta plantilla incluye instrucciones para el agente destino
        sobre cómo utilizar el contexto recuperado, enfatizando que
        debe guiar al estudiante en lugar de simplemente copiar
        el contenido.
        """
        return """[CONTEXTO PEDAGÓGICO RECUPERADO]
{documents}

[NOTA: Usa este contexto para enriquecer tu respuesta, pero sigue las reglas
pedagógicas del tutor. No copies el contenido directamente, úsalo para guiar
al estudiante con información precisa y actualizada.]
"""

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> RAGResult:
        """
        Recupera documentos relevantes para una consulta del estudiante.

        Este método orquesta el proceso completo de recuperación:

        1. Generación de embedding: Transforma la consulta textual en
           un vector de 384 dimensiones que captura su significado.

        2. Búsqueda vectorial: Consulta pgvector para encontrar los
           documentos más similares, aplicando filtros contextuales
           (unidad actual, materia, nivel de dificultad).

        3. Evaluación de confianza: Analiza los scores de similitud
           para determinar si el contexto recuperado es útil.

        4. Construcción de contexto: Formatea los documentos en un
           texto estructurado listo para ser prepuesto al prompt.

        En caso de errores (Ollama no disponible, error de DB), el
        método retorna un resultado vacío en lugar de propagar la
        excepción, asegurando que el flujo principal no se interrumpa.

        Args:
            query: Pregunta o mensaje del estudiante
            filters: Filtros contextuales opcionales:
                - unit: Unidad temática actual
                - materia_code: Código de materia
                - difficulty: Nivel del estudiante

        Returns:
            RAGResult con documentos, nivel de confianza, texto de
            contexto formateado, y el embedding de la query (útil
            para logging/debugging)
        """
        # 1. Generar embedding de la consulta
        try:
            query_embedding = await self.embeddings.embed(query)
        except Exception as e:
            logger.error(f"Error al generar embedding: {e}")
            return self._empty_result(query)

        # 2. Buscar documentos similares
        try:
            documents = await self.knowledge_repo.search_similar(
                query_embedding=query_embedding,
                filters=filters,
                limit=self.max_documents,
                min_similarity=self.min_confidence
            )
        except Exception as e:
            logger.error(f"Error al buscar documentos: {e}")
            return self._empty_result(query, query_embedding)

        # 3. Evaluar confianza
        confidence = self._evaluate_confidence(documents)
        is_sufficient = confidence in (RAGConfidence.HIGH, RAGConfidence.MEDIUM)

        # 4. Construir contexto solo si es suficiente
        context_text = self._build_context(documents) if is_sufficient else ""

        return RAGResult(
            documents=documents,
            confidence=confidence,
            is_sufficient=is_sufficient,
            context_text=context_text,
            query_embedding=query_embedding
        )

    def _evaluate_confidence(self, documents: List[Dict[str, Any]]) -> RAGConfidence:
        """
        Evalúa el nivel de confianza basado en las similitudes.

        La evaluación considera tanto el promedio de similitud
        (indica calidad general) como el máximo (indica si hay
        al menos un documento muy relevante). Pondera 60% promedio
        y 40% máximo para balancear ambos factores.
        """
        if not documents:
            return RAGConfidence.NONE

        avg_sim = sum(d["similarity"] for d in documents) / len(documents)
        max_sim = max(d["similarity"] for d in documents)

        # Ponderación: 60% promedio, 40% máximo
        score = (avg_sim * 0.6) + (max_sim * 0.4)

        if score >= self.CONFIDENCE_HIGH:
            return RAGConfidence.HIGH
        elif score >= self.CONFIDENCE_MEDIUM:
            return RAGConfidence.MEDIUM
        elif score >= self.CONFIDENCE_LOW:
            return RAGConfidence.LOW
        else:
            return RAGConfidence.NONE

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """
        Construye el texto de contexto a partir de los documentos.

        Cada documento se formatea incluyendo su tipo, título (si existe),
        resumen (si existe), y contenido (truncado a 1000 caracteres para
        evitar contextos excesivamente largos que degraden la respuesta).
        """
        if not documents:
            return ""

        doc_texts = []
        for i, doc in enumerate(documents, 1):
            doc_text = f"--- Documento {i} ({doc['content_type']}) ---\n"
            if doc.get("title"):
                doc_text += f"Título: {doc['title']}\n"
            if doc.get("summary"):
                doc_text += f"Resumen: {doc['summary']}\n"
            # Truncar contenido largo
            content = doc['content']
            if len(content) > 1000:
                content = content[:1000] + "..."
            doc_text += f"Contenido:\n{content}"
            doc_texts.append(doc_text)

        documents_text = "\n\n".join(doc_texts)
        return self.context_template.format(documents=documents_text)

    def _empty_result(
        self,
        query: str,
        embedding: Optional[List[float]] = None
    ) -> RAGResult:
        """Retorna un resultado vacío para casos de error o sin matches."""
        return RAGResult(
            documents=[],
            confidence=RAGConfidence.NONE,
            is_sufficient=False,
            context_text="",
            query_embedding=embedding or []
        )
```

---

## 5. Script de Ingesta de Documentos

### 5.1 El Proceso de Ingesta

Antes de que RAG pueda enriquecer las respuestas de los agentes, es necesario poblar la base de conocimiento con contenido académico. El script de ingesta automatiza este proceso, permitiendo cargar directorios completos de documentación en un solo comando.

El proceso de ingesta sigue un pipeline bien definido:

**Exploración del directorio**: El script recorre recursivamente el directorio especificado, identificando archivos con extensiones soportadas (.txt, .md, .json). Esto permite organizar el material en carpetas temáticas que el script respetará.

**Lectura y preprocesamiento**: Para cada archivo, se lee el contenido textual. El título del documento se deriva del nombre del archivo, transformando "quicksort_explicacion.md" en "Quicksort Explicación".

**Generación de embeddings**: El contenido de cada documento (truncado a 2000 caracteres para optimizar calidad del embedding) se envía a Ollama para generar su representación vectorial.

**Inserción en batch**: Los documentos procesados se acumulan y se insertan en la base de datos en una única transacción, optimizando el rendimiento cuando se cargan grandes cantidades de material.

```python
# backend/scripts/ingest_knowledge.py

"""
Script para ingestar documentos académicos al sistema RAG.

Este script facilita la carga inicial de contenido académico,
transformando archivos de texto y markdown en documentos
vectorizados listos para búsqueda semántica.

Ejemplos de uso:
    # Cargar toda la teoría de una materia
    python -m backend.scripts.ingest_knowledge --source ./docs/materiales --materia PROG1

    # Cargar una unidad específica
    python -m backend.scripts.ingest_knowledge --materia PROG1 --unit algoritmos --source ./teoria

    # Cargar ejemplos con dificultad avanzada
    python -m backend.scripts.ingest_knowledge --materia PROG1 --type ejemplo --difficulty avanzado --source ./ejemplos
"""

import asyncio
import argparse
from pathlib import Path
from typing import List, Dict
import json

from ..core.embeddings import OllamaEmbeddingProvider
from ..database.repositories.knowledge_repository import KnowledgeRepository
from ..database.config import get_db_session

# Extensiones de archivo soportadas
SUPPORTED_EXTENSIONS = {".txt", ".md", ".json"}

async def ingest_directory(
    source_path: Path,
    materia_code: str,
    unit: str = None,
    content_type: str = "teoria",
    difficulty: str = "intermedio"
):
    """
    Ingesta todos los documentos de un directorio.

    Recorre recursivamente el directorio, procesa cada archivo
    soportado, genera su embedding, y lo almacena en la base
    de conocimiento.
    """
    embedding_provider = OllamaEmbeddingProvider()

    with get_db_session() as session:
        repo = KnowledgeRepository(session)

        documents_to_create = []
        files = list(source_path.glob("**/*"))

        for file_path in files:
            # Filtrar solo archivos soportados
            if file_path.suffix not in SUPPORTED_EXTENSIONS:
                continue
            if file_path.is_dir():
                continue

            print(f"Procesando: {file_path}")

            # Leer contenido
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                print(f"  Error de encoding, saltando: {file_path}")
                continue

            # Extraer título del nombre del archivo
            title = file_path.stem.replace("_", " ").replace("-", " ").title()

            # Generar embedding (usando primeros 2000 chars)
            text_for_embedding = content[:2000] if len(content) > 2000 else content
            embedding = await embedding_provider.embed(text_for_embedding)

            # Determinar unidad de la estructura de carpetas si no se especifica
            inferred_unit = unit or file_path.parent.name

            # Preparar documento
            doc = {
                "content": content,
                "title": title,
                "content_type": content_type,
                "unit": inferred_unit,
                "difficulty": difficulty,
                "materia_code": materia_code,
                "source_file": str(file_path),
                "embedding": embedding
            }
            documents_to_create.append(doc)

        # Insertar en batch
        if documents_to_create:
            count = repo.bulk_create_with_embeddings(documents_to_create)
            print(f"\nInsertados {count} documentos exitosamente")
        else:
            print("\nNo se encontraron documentos para procesar")

    await embedding_provider.close()

def main():
    parser = argparse.ArgumentParser(
        description="Ingestar documentos académicos para RAG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python -m backend.scripts.ingest_knowledge --source ./teoria --materia PROG1
  python -m backend.scripts.ingest_knowledge --source ./ejemplos --materia PROG1 --type ejemplo
  python -m backend.scripts.ingest_knowledge --source ./faqs --materia PROG1 --type faq --unit general
        """
    )
    parser.add_argument("--source", required=True, help="Directorio fuente con los documentos")
    parser.add_argument("--materia", required=True, help="Código de materia (ej: PROG1)")
    parser.add_argument("--unit", help="Unidad temática (default: nombre de carpeta)")
    parser.add_argument("--type", default="teoria",
                       choices=["teoria", "ejemplo", "faq", "consigna", "ejercicio"],
                       help="Tipo de contenido")
    parser.add_argument("--difficulty", default="intermedio",
                       choices=["basico", "intermedio", "avanzado"],
                       help="Nivel de dificultad")

    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        print(f"Error: El directorio {source} no existe")
        return

    asyncio.run(ingest_directory(
        source_path=source,
        materia_code=args.materia,
        unit=args.unit,
        content_type=args.type,
        difficulty=args.difficulty
    ))

if __name__ == "__main__":
    main()
```

---

## 6. Integración con Agentes Existentes

### 6.1 El Tutor (T-IA-Cog): Enriquecimiento Sin Modificación

Uno de los aspectos más elegantes de esta propuesta es que el agente Tutor no requiere ningún cambio en su código interno. La integración de RAG ocurre en una capa superior (AIGateway), de modo que el Tutor simplemente recibe un prompt más informativo sin saber de dónde proviene esa información adicional.

Consideremos cómo se vería un prompt enriquecido desde la perspectiva del Tutor:

```
[CONTEXTO PEDAGÓGICO RECUPERADO]
--- Documento 1 (teoria) ---
Título: Quicksort Explicación
Contenido:
Quicksort es un algoritmo de ordenamiento basado en la estrategia
divide y vencerás. Funciona eligiendo un elemento "pivote" y
particionando el array en dos subarrays: elementos menores al
pivote y elementos mayores. Luego ordena recursivamente ambos
subarrays. Su complejidad promedio es O(n log n), aunque en el
peor caso (array ya ordenado con pivote mal elegido) puede
degradar a O(n²).

--- Documento 2 (ejemplo) ---
Título: Quicksort Python
Contenido:
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

[NOTA: Usa este contexto para enriquecer tu respuesta, pero sigue
las reglas pedagógicas del tutor. No copies el contenido directamente,
úsalo para guiar al estudiante con información precisa y actualizada.]

[PREGUNTA DEL ESTUDIANTE]
No entiendo cómo funciona quicksort
```

El Tutor procesa este prompt completo aplicando sus reglas pedagógicas habituales. Si está en modo socrático, utilizará el conocimiento contextual para formular preguntas guía más precisas: "Cuando tienes una lista desordenada y eliges un elemento como 'pivote', ¿qué crees que sucede con los elementos menores que él? ¿Y con los mayores?". El Tutor no copia directamente la explicación; la usa como base para guiar el descubrimiento del estudiante.

La lógica interna del Tutor —sus cuatro modos de operación (socrático, explicativo, guiado, metacognitivo), sus semáforos de control, sus reglas de transición— permanece exactamente igual. Simplemente tiene más información para trabajar.

### 6.2 Los Simuladores (S-IA-X): Documentación Técnica en Contexto

Los simuladores de roles profesionales también se benefician de la integración RAG, aunque con un enfoque diferente. Mientras el Tutor necesita teoría pedagógica, los simuladores necesitan documentación técnica actualizada.

Por ejemplo, cuando un estudiante interactúa con el simulador de Tech Interviewer y propone una arquitectura utilizando patrones de diseño, RAG puede inyectar documentación relevante:

```
[CONTEXTO TÉCNICO]
--- Documento 1 (documentacion) ---
Título: Patrón Factory Method
Contenido:
Factory Method define una interfaz para crear objetos, pero
permite a las subclases decidir qué clase instanciar. Útil
cuando una clase no puede anticipar el tipo de objetos que
debe crear, o cuando quieres delegar la responsabilidad de
creación a subclases especializadas.

[PROPUESTA DEL ESTUDIANTE]
Propongo usar el patrón Factory para la creación de conexiones
a la base de datos...
```

El simulador, actuando como un Tech Interviewer experimentado, puede entonces hacer preguntas informadas sobre la propuesta: "Interesante elección. ¿Por qué Factory Method en lugar de Abstract Factory? ¿Cómo manejarías el caso donde necesitas crear familias de objetos relacionados?".

### 6.3 Agentes que No Utilizan RAG

No todos los agentes del sistema se benefician de la integración RAG. La siguiente tabla clarifica qué agentes lo utilizan y por qué:

| Agente | ¿Usa RAG? | Justificación |
|--------|-----------|---------------|
| T-IA-Cog (Tutor) | **Sí** | Necesita teoría y ejemplos para guiar pedagógicamente |
| S-IA-X (Simuladores) | **Sí** | Requiere documentación técnica para roles profesionales |
| E-IA-Proc (Evaluador) | No | Evalúa trazas cognitivas, no necesita conocimiento externo |
| AR-IA (Analista de Riesgos) | No | Analiza patrones de comportamiento, no contenido académico |
| GOV-IA (Gobernanza) | No | Aplica reglas fijas, no requiere conocimiento contextual |
| TC-N4 (Trazabilidad) | No | Registra eventos, no genera contenido |

Los agentes que no usan RAG se benefician indirectamente: si T-IA-Cog genera mejores respuestas gracias al contexto enriquecido, el evaluador tendrá interacciones de mayor calidad que evaluar, y el trazador registrará un proceso de aprendizaje más coherente.

---

## 7. Configuración y Variables de Entorno

La integración RAG introduce nuevas variables de configuración que deben agregarse al archivo `.env` del sistema. Estas variables controlan el comportamiento de los componentes RAG y permiten ajustar su operación sin modificar código.

```bash
# .env (nuevas variables para RAG)

# === Configuración General de RAG ===
# Master switch: habilita/deshabilita RAG globalmente
RAG_ENABLED=true

# Umbral mínimo de similitud para usar contexto (0.0-1.0)
# Valores más altos = solo contexto muy relevante
RAG_MIN_CONFIDENCE=0.6

# Máximo de documentos a incluir en contexto
RAG_MAX_DOCUMENTS=3

# === Configuración de Ollama para Embeddings ===
# URL del servidor Ollama (cambiar si está en Docker)
OLLAMA_EMBEDDINGS_URL=http://localhost:11434

# Modelo de embeddings (nomic-embed-text es el recomendado)
OLLAMA_EMBEDDINGS_MODEL=nomic-embed-text

# === PostgreSQL con pgvector ===
# Utiliza la misma conexión existente
# La extensión vector se habilita automáticamente en la migración
# DATABASE_URL=postgresql://...
```

Estas variables permiten diferentes configuraciones para diferentes ambientes:

**Desarrollo local**: RAG habilitado con umbrales bajos para probar recuperación
```bash
RAG_ENABLED=true
RAG_MIN_CONFIDENCE=0.4
OLLAMA_EMBEDDINGS_URL=http://localhost:11434
```

**Staging**: RAG habilitado con umbrales moderados
```bash
RAG_ENABLED=true
RAG_MIN_CONFIDENCE=0.6
OLLAMA_EMBEDDINGS_URL=http://ollama:11434  # Docker network
```

**Producción inicial**: RAG habilitado con umbrales altos (conservador)
```bash
RAG_ENABLED=true
RAG_MIN_CONFIDENCE=0.75
RAG_MAX_DOCUMENTS=2
```

---

## 8. Plan de Implementación

La implementación de RAG se estructura en cinco fases progresivas, diseñadas para minimizar riesgos y permitir validación en cada etapa.

### Fase 1: Infraestructura

La primera fase establece los cimientos técnicos sobre los cuales operará todo el sistema RAG. Involucra tareas de DevOps y configuración de servicios.

Las tareas específicas incluyen:

- **Actualizar imagen de PostgreSQL**: Reemplazar la imagen actual por `pgvector/pgvector:pg15` que incluye la extensión de vectores precompilada.

- **Ejecutar migración de base de datos**: Aplicar el script `add_knowledge_rag.py` que crea la tabla `knowledge_documents` con su columna vector e índices.

- **Agregar Ollama al stack**: Si no existe en el docker-compose, agregar el servicio Ollama con volumen persistente para modelos descargados.

- **Descargar modelo de embeddings**: Ejecutar `ollama pull nomic-embed-text` para obtener el modelo de vectorización.

- **Validar conectividad**: Verificar que la API puede conectarse tanto a pgvector como a Ollama.

### Fase 2: Componentes Core

La segunda fase implementa los cuatro nuevos componentes: EmbeddingProvider, KnowledgeRepository, KnowledgeDocument, y KnowledgeRAGAgent. Esta es la fase de mayor desarrollo de código nuevo.

Las entregas esperadas son:

- Implementación completa de `OllamaEmbeddingProvider` con cache Redis
- Implementación de `KnowledgeRepository` con búsqueda vectorial
- Modelo ORM `KnowledgeDocumentDB` registrado en el sistema
- Implementación del `KnowledgeRAGAgent` con evaluación de confianza
- Suite de tests unitarios para cada componente

### Fase 3: Integración

La tercera fase conecta los componentes nuevos con el sistema existente, específicamente modificando el AIGateway para inyectar el agente RAG.

Los entregables incluyen:

- Modificación del constructor de AIGateway para aceptar KnowledgeRAGAgent
- Implementación del flujo de enriquecimiento de prompts
- Feature flag `RAG_ENABLED` funcional
- Tests de integración que validen el flujo completo
- Documentación de la API interna

### Fase 4: Ingesta y Datos

Con la infraestructura técnica en su lugar, la cuarta fase se enfoca en poblar la base de conocimiento con contenido académico real.

Las actividades incluyen:

- Crear script `ingest_knowledge.py` con CLI completa
- Definir estructura de directorios para material académico
- Cargar corpus inicial de teoría y ejemplos
- Validar calidad de búsquedas con queries reales
- Ajustar umbrales basándose en resultados observados

### Fase 5: Observabilidad

La fase final agrega instrumentación para monitorear el comportamiento de RAG en producción.

Los componentes de observabilidad incluyen:

- Métricas Prometheus: latencia de RAG, cache hit rate, distribución de confianza
- Dashboard Grafana: visualización de métricas clave
- Logs estructurados: registro de queries, documentos recuperados, decisiones de suficiencia
- Alertas: notificaciones cuando la latencia o tasa de errores exceden umbrales

---

## 9. Riesgos y Mitigaciones

Toda implementación de software conlleva riesgos. La siguiente tabla identifica los principales riesgos de la integración RAG junto con las estrategias de mitigación diseñadas para cada uno.

| Riesgo | Impacto | Probabilidad | Mitigación |
|--------|---------|--------------|------------|
| **Ollama no disponible** | Alto | Baja | Fallback a flujo sin RAG. El feature flag permite continuar sin el servicio. El sistema registra warning pero no falla. |
| **Latencia de embeddings excesiva** | Medio | Media | Cache agresivo en Redis reduce llamadas repetidas. Timeouts configurables evitan bloqueos prolongados. |
| **Documentos recuperados irrelevantes** | Medio | Media | Umbral de confianza configurable filtra resultados de baja calidad. Métricas permiten ajustar umbrales. |
| **pgvector lento con muchos vectores** | Bajo | Baja | Índice IVFFlat optimizado. Para >1M documentos, migrar a HNSW. |
| **Contexto demasiado largo** | Medio | Media | Límite de 3 documentos por defecto. Truncamiento a 1000 chars por documento. Template configurable. |
| **Contenido desactualizado** | Bajo | Media | Script de re-ingesta permite actualizar corpus. Metadatos incluyen fecha de creación. |

La mitigación más importante es el diseño de "fallo seguro": si cualquier componente de RAG falla, el sistema continúa operando exactamente como lo hacía antes de la integración. El estudiante nunca verá un error; simplemente recibirá una respuesta sin enriquecimiento contextual.

---

## 10. Métricas de Éxito

Para evaluar la efectividad de la integración RAG, se definen métricas cuantitativas con objetivos claros y métodos de medición especificados.

| Métrica | Objetivo | Método de Medición |
|---------|----------|-------------------|
| **Latencia RAG** | < 100ms p95 | Histogram Prometheus midiendo tiempo desde query hasta respuesta |
| **Cache hit rate** | > 60% | Contador de hits/misses en Redis |
| **Confianza promedio** | > 0.7 | Histogram de scores de similitud de documentos recuperados |
| **Cobertura de uso** | > 80% sesiones | Porcentaje de interacciones donde RAG provee contexto suficiente |
| **Satisfacción docente** | > 4/5 | Encuesta semestral a docentes sobre calidad de respuestas |
| **Reducción de "no sé"** | -30% | Comparación de frecuencia de respuestas donde el agente no puede ayudar |

Estas métricas se revisarán semanalmente durante el primer mes de producción y mensualmente después de la estabilización.

---

## 11. Conclusión

La integración de Retrieval-Augmented Generation al sistema de agentes AI-Native representa una evolución natural de la arquitectura existente, no una revolución disruptiva. Al diseñar RAG como una capa de enriquecimiento que opera **antes** de los agentes existentes, logramos mejorar significativamente la calidad de las respuestas sin arriesgar la estabilidad del sistema actual.

Los cinco pilares que garantizan el éxito de esta integración son:

**Aditividad**: RAG se agrega al sistema sin modificar la lógica interna de ningún agente existente. El Tutor, los Simuladores, el Evaluador — todos continúan operando exactamente como lo hacen hoy. Simplemente reciben información más rica para trabajar.

**Desacoplamiento**: El feature flag `RAG_ENABLED` permite activar o desactivar la funcionalidad instantáneamente, sin necesidad de redespliegue. Si surge cualquier problema en producción, un cambio de configuración restaura el comportamiento original.

**Economía**: La combinación de pgvector (incluido en PostgreSQL) con Ollama (gratuito y local) elimina costos adicionales de infraestructura o APIs externas. El único costo es computacional, y es marginal comparado con el procesamiento LLM existente.

**Escalabilidad**: pgvector con índices IVFFlat soporta eficientemente hasta un millón de vectores. Más allá de ese umbral, la migración a índices HNSW mantiene el rendimiento. El cache Redis reduce la carga en Ollama para queries repetitivas.

**Auditabilidad**: Cada interacción que utiliza RAG queda registrada en las trazas del sistema, incluyendo qué documentos fueron recuperados, con qué nivel de confianza, y si fueron incluidos en el contexto. Esto facilita tanto el debugging como la mejora continua del corpus de conocimiento.

El resultado esperado es un sistema que mantiene todas las garantías pedagógicas del diseño actual —evaluación basada en proceso, trazabilidad N4, modos de tutoría adaptativos— mientras proporciona respuestas más fundamentadas, precisas y alineadas con el contenido específico de cada asignatura.

La implementación propuesta puede ejecutarse de manera incremental, con validación en cada fase, y con la seguridad de que el sistema existente nunca dejará de funcionar incluso si RAG experimenta problemas. Es una mejora de bajo riesgo y alto potencial.

---

*Documento generado: Enero 2026*
*Autor: Cortez87*
*Revisión: Enero 2026*
