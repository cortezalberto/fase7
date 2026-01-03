# Análisis de Factibilidad: Propuesta RAG rag1.txt

**Autor**: Claude Code (Análisis Técnico)
**Fecha**: 3 de enero de 2026
**Documento Analizado**: `rag1.txt` (~2,800 líneas)
**Estado del Proyecto Actual**: Post-Cortez71 (71 auditorías completadas)

---

## Resumen Ejecutivo

La propuesta contenida en `rag1.txt` presenta una refactorización significativa del sistema AI-Native MVP orientada a tres objetivos fundamentales: establecer un catálogo académico jerárquico (Materia → Unidad → Actividad → Ejercicio), implementar un sistema RAG completo con pgvector para retrieval semántico de documentos, e introducir un modelo de trazabilidad basado en event sourcing para las interacciones con IA.

**Veredicto**: La propuesta es **técnicamente factible** pero requiere una estrategia de migración cuidadosamente planificada. El sistema actual tiene una arquitectura madura con 6 agentes de IA, trazabilidad N4, y más de 70 auditorías de calidad completadas. Una refactorización total sería contraproducente; en cambio, se recomienda una **integración incremental** que aproveche la infraestructura existente.

---

## 1. Análisis de la Propuesta

### 1.1 Los Dos Mundos Conceptuales

La propuesta divide el sistema en dos dominios claramente separados:

**Mundo Académico (Estático)**: Representa el contenido curricular que los docentes crean y mantienen. Este mundo es relativamente estable y cambia solo cuando el docente actualiza materiales o estructura del curso. La jerarquía propuesta es:

```
Materia (ej: "Programación I")
  └── Unidad (ej: "Unidad 3: Estructuras de Control")
        ├── Documentos (ENUNCIADO + MATERIALES en PDF)
        └── Actividades
              └── Ejercicios
                    ├── Historia de Usuario (HU)
                    ├── Criterios de Aceptación (CA)
                    └── Rúbrica de Evaluación
```

**Mundo de Ejecución (Dinámico)**: Representa todo lo que ocurre cuando un estudiante interactúa con el sistema. Incluye sesiones de trabajo, entregas de código, interacciones con IA, y el historial completo de intentos y evaluaciones.

Esta separación conceptual es sólida y alineada con principios de diseño orientado al dominio (DDD). Sin embargo, el sistema actual ya maneja gran parte de esta distinción a través del modelo de Actividades y Sesiones, aunque con una granularidad diferente.

### 1.2 Estructura de Datos del Catálogo Académico

La propuesta introduce un modelo relacional nuevo con las siguientes entidades principales:

**Tablas de Catálogo**:
- `materia`: Asignatura con código, nombre, y descripción
- `unidad`: División temática dentro de una materia, con orden secuencial
- `actividad`: Trabajo práctico que agrupa ejercicios relacionados
- `ejercicio`: Problema individual con título, descripción base, y configuración

**Tablas de Contenido Pedagógico**:
- `ejercicio_hu`: Historia de Usuario en formato "Como [rol], quiero [acción], para [beneficio]"
- `ejercicio_ca`: Criterios de Aceptación como lista ordenada de condiciones verificables
- `ejercicio_rubrica`: Rúbrica de evaluación con dimensiones y niveles ponderados

**Tablas de Documentación**:
- `unidad_documento`: Metadatos de PDFs (enunciados y materiales de apoyo)
- `documento_ingesta`: Historial versionado de procesamiento de documentos
- `documento_chunk`: Fragmentos de texto con embeddings vectoriales

Esta estructura es más granular que el modelo actual. El sistema existente tiene `ActivityDB` con políticas (`PolicyConfig`) pero carece del nivel de `Materia` y `Unidad`, y no tiene el patrón HU+CA+Rúbrica explícito.

### 1.3 Sistema RAG con pgvector

El corazón técnico de la propuesta es la implementación de Retrieval-Augmented Generation usando PostgreSQL con la extensión pgvector. El flujo propuesto es:

1. **Ingesta de Documentos**: El docente sube PDFs que se almacenan en MinIO (object storage S3-compatible). El sistema extrae texto usando PyMuPDF, lo divide en chunks de ~1200 caracteres con overlap de 150 caracteres, y genera embeddings de 1536 dimensiones.

2. **Almacenamiento Vectorial**: Los chunks con sus embeddings se guardan en la tabla `documento_chunk` con índices HNSW para búsqueda eficiente por similitud coseno.

3. **Retrieval Contextual**: Cuando un estudiante hace una consulta, el sistema convierte la pregunta en un vector, busca los chunks más similares filtrados por unidad, y construye un contexto enriquecido.

4. **Rehidratación de Contexto**: El sistema ensambla automáticamente: HU + CA del ejercicio + última entrega del estudiante + resumen de sesión previa + top-K chunks relevantes del RAG.

Esta arquitectura es robusta y sigue las mejores prácticas de sistemas RAG modernos. El uso de pgvector en lugar de bases vectoriales dedicadas (Pinecone, Weaviate) es una decisión pragmática que simplifica la infraestructura y reduce costos.

### 1.4 Event Sourcing para Trazabilidad de IA

La propuesta introduce un modelo de event sourcing "ligero" para capturar todas las interacciones con IA:

```sql
CREATE TYPE ai_event_type AS ENUM (
  'PROMPT_SUBMITTED',   -- Estudiante envía consulta
  'RAG_RETRIEVAL',      -- Sistema recupera documentos relevantes
  'MODEL_RESPONSE',     -- LLM genera respuesta
  'CODE_SNAPSHOT',      -- Captura de código en momento específico
  'EVAL_REQUESTED',     -- Se solicita evaluación
  'EVAL_RESULT',        -- Resultado de evaluación
  'RISK_FLAGGED',       -- Detección de riesgo
  'HUMAN_FEEDBACK'      -- Retroalimentación del docente
);
```

Cada evento incluye: estudiante_id, sesion_id, ejercicio_id, timestamp, y un payload JSON con los detalles específicos del evento.

Este modelo es compatible y complementario con el sistema de trazabilidad N4 existente. De hecho, representa una evolución hacia un modelo más auditable donde cada interacción queda registrada como un evento inmutable.

### 1.5 Flujo de Trabajo del Estudiante

La propuesta define un ciclo de vida claro para el progreso del estudiante:

**Estados del Ejercicio**:
```
NO_INICIADO → EN_PROGRESO → FINALIZADO → REENVIO → VALIDADO
```

**Componentes de Contexto** (estrategia de rehidratación):
- **Nivel A (Fijo)**: HU, CA, rúbrica del ejercicio
- **Nivel B (Estado)**: Estado actual, intentos, score
- **Nivel C (Memoria)**: Última entrega, resumen de sesión, chunks RAG

Esta estrategia de tres niveles permite construir prompts contextualizados que mantienen coherencia a través de múltiples interacciones, algo que el sistema actual logra parcialmente a través del `TrainingTraceCollector`.

---

## 2. Comparación con el Sistema Actual

### 2.1 Arquitectura Actual (Post-Cortez71)

El sistema actual tiene una arquitectura madura:

**6 Agentes de IA**:
- T-IA-Cog (Tutor Cognitivo con 5 modos pedagógicos)
- E-IA-Proc (Evaluador de Proceso)
- S-IA-X (Simuladores Profesionales - 11 roles)
- AR-IA (Analista de Riesgos 5D)
- GOV-IA (Gobernanza y Delegación)
- TC-N4 (Trazabilidad N4)

**Trazabilidad N4**: Sistema de 4 niveles (N1: raw, N2: preprocesado, N3: LLM, N4: sintetizado) con 8 estados cognitivos y análisis de dependencia de IA.

**Digital Trainer**: Sistema de entrenamiento con ejercicios, hints contextuales, y evaluación de código usando el agente T-IA-Cog.

**Modelo de Datos Actual**:
- `SessionDB`, `CognitiveTraceDB`, `TraceSequenceDB`
- `ActivityDB` con `PolicyConfig` (límites de hints, penalizaciones)
- `ExerciseDB`, `HintDB`, `TestDB`, `AttemptDB`
- `UserDB` con contexto académico (course_name, commission)

### 2.2 Brechas y Oportunidades

| Aspecto | Sistema Actual | Propuesta RAG | Análisis |
|---------|---------------|---------------|----------|
| **Jerarquía Académica** | ActivityDB plano | Materia→Unidad→Actividad→Ejercicio | Propuesta añade estructura necesaria |
| **Documentos** | No estructurado | PDF ingesta + chunking | Propuesta superior |
| **Retrieval Semántico** | No existe | pgvector + embeddings | Necesario para RAG |
| **HU/CA Pattern** | Descripción libre en ejercicios | Estructura formal separada | Propuesta mejora claridad |
| **Rúbricas** | RubricLevelDB simple | ejercicio_rubrica con versiones | Propuesta más completa |
| **Trazabilidad** | N4 con estados cognitivos | Event sourcing ai_event | Complementarios |
| **Agentes IA** | 6 agentes especializados | Solo RAG + retrieval | Sistema actual superior |
| **Evaluación Proceso** | E-IA-Proc completo | No especificado | Sistema actual superior |
| **Simuladores** | 11 roles profesionales | No incluidos | Sistema actual superior |
| **Gestión Riesgos** | AR-IA 5D + alertas | risk_flagged básico | Sistema actual superior |

### 2.3 Lo que la Propuesta NO Incluye

La propuesta de `rag1.txt` es fundamentalmente una capa de **datos y retrieval**. No aborda:

1. **Lógica de Agentes**: Los 6 agentes actuales (especialmente T-IA-Cog con sus 5 modos pedagógicos) no tienen equivalente en la propuesta.

2. **Evaluación de Proceso**: El sistema E-IA-Proc que analiza "cómo" el estudiante resuelve problemas está ausente.

3. **Simuladores Profesionales**: Los 11 simuladores de roles profesionales (Product Owner, Scrum Master, Tech Interviewer, etc.) no se mencionan.

4. **Análisis de Riesgos 5D**: El modelo sofisticado de riesgo con dimensiones cognitiva, ética, epistémica, técnica y de gobernanza no está presente.

5. **Gobernanza de IA**: El sistema de semáforos (verde/amarillo/rojo) para control de autonomía del estudiante no se incluye.

6. **Integración LTI/Moodle**: La infraestructura de Cortez65.1/65.2 para integración con Moodle no se considera.

---

## 3. Estrategia de Migración Recomendada

### 3.1 Principio Fundamental: Integración, No Reemplazo

Dado el nivel de madurez del sistema actual (71 auditorías, arquitectura estable, agentes funcionando), una refactorización total sería destructiva. En cambio, se recomienda **integrar** los componentes valiosos de la propuesta RAG como una capa adicional.

### 3.2 Fases de Implementación

**Fase 1: Infraestructura pgvector (2-3 semanas de desarrollo)**

Esta fase establece la base técnica para RAG sin modificar el sistema existente.

Tareas:
1. Agregar extensión pgvector a PostgreSQL (ya documentado en stack.md como recomendación)
2. Crear migración para tabla `documento_chunk` con índice HNSW
3. Implementar servicio de embeddings (nomic-embed-text via Ollama, dimensión 384)
4. Crear pipeline básico de ingesta PDF → chunks → embeddings

Archivos a crear:
- `backend/database/models/rag.py`: DocumentoChunkDB, IngestaDB
- `backend/database/repositories/rag_repository.py`
- `backend/services/embedding_service.py`
- `backend/services/pdf_ingestion_service.py`
- Migración Alembic: `add_pgvector_support.py`

**Fase 2: Catálogo Académico Extendido (1-2 semanas)**

Esta fase añade la jerarquía Materia→Unidad sin romper el modelo actual de Activities.

Estrategia de integración:
- `MateriaDB` se relaciona con el `course_name` de UserDB
- `UnidadDB` agrupa actividades existentes (ActivityDB.unidad_id nullable para migración gradual)
- Mantener ActivityDB como está, añadir foreign key opcional a UnidadDB

Archivos a crear/modificar:
- `backend/database/models/academic_catalog.py`: MateriaDB, UnidadDB
- `backend/database/repositories/catalog_repository.py`
- Modificar `ActivityDB`: añadir `unidad_id` opcional
- Migración: `add_academic_catalog.py`

**Fase 3: Patrón HU+CA para Ejercicios (1 semana)**

Enriquecer el modelo de ejercicios existente con el patrón de Historia de Usuario y Criterios de Aceptación.

Estrategia:
- Añadir campos a ExerciseDB en lugar de crear tablas separadas
- `ExerciseDB.historia_usuario`: Text nullable
- `ExerciseDB.criterios_aceptacion`: JSON array de strings
- Mantener compatibilidad con ejercicios existentes que no tengan HU/CA

**Fase 4: Integración RAG con AIGateway (2 semanas)**

Esta es la fase crítica donde el RAG se conecta con el sistema de agentes existente.

Modificaciones a AIGateway:
1. Añadir paso de retrieval antes de generar respuestas
2. El contexto rehidratado se incorpora al prompt del agente T-IA-Cog
3. Los eventos RAG_RETRIEVAL se registran en el sistema de trazabilidad N4 existente

```python
# Pseudocódigo de integración
class AIGateway:
    async def process_interaction(self, request):
        # 1. CRPE clasifica el prompt (existente)
        classification = self.cognitive_engine.classify(request.prompt)

        # 2. NUEVO: RAG retrieval si hay documentos disponibles
        if self.should_use_rag(request):
            rag_context = await self.rag_service.retrieve(
                unidad_id=request.unidad_id,
                query=request.prompt
            )
            request = request.with_rag_context(rag_context)

        # 3. Agente genera respuesta (existente, pero con contexto enriquecido)
        response = await self.tutor_agent.generate(request)

        # 4. Trazabilidad (existente + eventos RAG)
        await self.trace_coordinator.record(request, response)
```

**Fase 5: Event Sourcing Complementario (1 semana)**

Integrar el modelo de ai_event como complemento a la trazabilidad N4.

Estrategia:
- La tabla `ai_event` captura eventos atómicos
- Los traces N4 se construyen agregando eventos relacionados
- Ambos sistemas coexisten: eventos para auditoría detallada, N4 para análisis cognitivo

**Fase 6: MinIO para Storage de Documentos (1 semana)**

Migrar almacenamiento de PDFs y entregas a MinIO.

Tareas:
- Desplegar MinIO en docker-compose
- Implementar StorageService abstracto (local → MinIO)
- Migrar documentos existentes (si los hay)

### 3.3 Lo que NO se Implementa de la Propuesta

Algunos elementos de `rag1.txt` no se implementan porque el sistema actual ya tiene soluciones superiores:

1. **Modelo de estudiante simplificado**: El sistema actual tiene `UserDB` con roles, verificación, y contexto académico (Cortez65.2). No se reemplaza.

2. **Estados de ejercicio básicos**: El sistema actual tiene un modelo más rico con `AttemptDB`, `SessionDB`, y estados cognitivos. Se mantiene.

3. **Rúbricas desde cero**: El sistema actual tiene `RubricLevelDB`. Se extiende en lugar de reemplazar.

4. **Sesiones de trabajo independientes**: Las sesiones existentes (`SessionDB`) tienen integración profunda con agentes y trazabilidad. Se mantienen.

---

## 4. Análisis de Riesgos de la Migración

### 4.1 Riesgos Técnicos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| pgvector degradación performance con muchos chunks | Media | Alto | Índices HNSW, particionado por unidad |
| Inconsistencia entre trazabilidad N4 y ai_event | Alta | Medio | Wrapper que sincroniza ambos sistemas |
| Embeddings de baja calidad con nomic-embed-text | Baja | Medio | Benchmarks antes de producción |
| MinIO punto único de falla | Media | Alto | Configurar replicación |
| Migraciones complejas rompen datos existentes | Media | Crítico | Backups automáticos, migraciones reversibles |

### 4.2 Riesgos de Negocio

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Docentes no adoptan carga de PDFs | Alta | Alto | Interface simple, templates |
| Estudiantes confundidos por respuestas con RAG | Media | Medio | Indicadores claros de fuentes |
| Tiempo de respuesta aumenta con retrieval | Media | Medio | Caché, embeddings precalculados |

### 4.3 Riesgos de Proyecto

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Scope creep: "ya que estamos, cambiemos todo" | Alta | Crítico | Fases estrictas, feature flags |
| Regresiones en funcionalidad existente | Media | Alto | Tests automatizados antes de cada fase |
| Documentación desactualizada | Alta | Medio | Actualizar CLAUDE.md en cada fase |

---

## 5. Estimación de Esfuerzo

### 5.1 Desglose por Fase

| Fase | Esfuerzo Backend | Esfuerzo Frontend | Testing | Total |
|------|-----------------|-------------------|---------|-------|
| 1. pgvector | 2 semanas | 0 | 3 días | ~2.5 semanas |
| 2. Catálogo | 1 semana | 3 días | 2 días | ~1.5 semanas |
| 3. HU+CA | 3 días | 2 días | 1 día | ~1 semana |
| 4. RAG+AIGateway | 2 semanas | 1 semana | 4 días | ~3 semanas |
| 5. Event Sourcing | 1 semana | 2 días | 2 días | ~1.5 semanas |
| 6. MinIO | 3 días | 1 día | 1 día | ~1 semana |
| **Total** | ~7 semanas | ~2 semanas | ~2 semanas | **~11 semanas** |

### 5.2 Dependencias Técnicas Nuevas

```
pip install:
  pgvector>=0.2.0
  pymupdf>=1.23.0
  minio>=7.2.0
  tiktoken>=0.5.0  # opcional para conteo de tokens

Docker:
  - MinIO (minio/minio:latest)
  - PostgreSQL con pgvector (pgvector/pgvector:pg16)
```

---

## 6. Conclusiones y Recomendaciones

### 6.1 La Propuesta es Valiosa pero Incompleta

El documento `rag1.txt` presenta ideas sólidas sobre estructura de datos y retrieval semántico, pero es fundamentalmente una propuesta de **capa de datos**, no una arquitectura completa. No considera los 6 agentes de IA, la trazabilidad N4, los simuladores profesionales, ni el análisis de riesgos 5D que hacen único al sistema actual.

### 6.2 Recomendación: Integración Selectiva

Se recomienda **adoptar selectivamente** los siguientes componentes:

**Adoptar**:
- pgvector para embeddings y retrieval semántico
- Jerarquía Materia→Unidad como extensión del catálogo
- Patrón HU+CA para enriquecer descripción de ejercicios
- Pipeline de ingesta PDF para documentación de cursos
- MinIO para almacenamiento de archivos

**No Adoptar** (sistema actual superior):
- Modelo de sesiones simplificado
- Estados de ejercicio básicos
- Trazabilidad basada solo en events (mantener N4)
- Modelo de estudiante reducido

### 6.3 Próximos Pasos Concretos

1. **Crear branch `feature/rag-integration`** para desarrollo aislado
2. **Fase 1 primero**: Probar pgvector con datos de prueba antes de integrar
3. **Feature flags**: `RAG_ENABLED=false` por defecto hasta validación completa
4. **Métricas de calidad RAG**: Implementar evaluación de relevancia de chunks
5. **Documentación continua**: Actualizar CLAUDE.md en cada fase

### 6.4 Veredicto Final

**FACTIBLE con condiciones**. La propuesta puede integrarse al sistema existente siguiendo una estrategia de fases incrementales. El resultado final será un sistema más potente que combina:
- La estructura de datos y RAG de la propuesta
- Los 6 agentes de IA del sistema actual
- La trazabilidad N4 enriquecida con eventos RAG
- Los simuladores profesionales intactos

El esfuerzo estimado de ~11 semanas es significativo pero manejable. La clave del éxito es resistir la tentación de "reescribir todo" y en cambio integrar quirúrgicamente los componentes de valor.

---

## Apéndice A: Mapeo de Tablas Propuestas vs Existentes

| Tabla Propuesta | Equivalente Actual | Acción Recomendada |
|-----------------|-------------------|-------------------|
| materia | course_name en UserDB | Crear MateriaDB |
| unidad | No existe | Crear UnidadDB |
| actividad | ActivityDB | Extender ActivityDB |
| ejercicio | ExerciseDB | Extender ExerciseDB |
| ejercicio_hu | exercise.description | Añadir campo |
| ejercicio_ca | No existe | Añadir campo JSON |
| ejercicio_rubrica | RubricLevelDB | Extender modelo |
| unidad_documento | No existe | Crear modelo |
| documento_ingesta | No existe | Crear modelo |
| documento_chunk | No existe | Crear modelo |
| estudiante | UserDB | No cambiar |
| sesion_trabajo | SessionDB | No cambiar |
| ejercicio_estudiante | AttemptDB + progreso | Extender |
| entrega_ejercicio | AttemptDB | Extender |
| ai_event | CognitiveTraceDB | Complementar |

## Apéndice B: SQL de Migración Inicial para pgvector

```sql
-- Migración 0001: Habilitar pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Migración 0002: Tabla de chunks con embeddings
CREATE TABLE documento_chunk (
    id BIGSERIAL PRIMARY KEY,
    unidad_id BIGINT NOT NULL,
    documento_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    page_from INT,
    page_to INT,
    content_text TEXT NOT NULL,
    embedding vector(384) NOT NULL,  -- nomic-embed-text usa 384 dims
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chunk_doc_idx UNIQUE (documento_id, chunk_index)
);

-- Índice HNSW para búsqueda por similitud coseno
CREATE INDEX idx_chunk_embedding ON documento_chunk
    USING hnsw (embedding vector_cosine_ops);

-- Índice para filtrar por unidad
CREATE INDEX idx_chunk_unidad ON documento_chunk (unidad_id);
```

---

*Documento generado por Claude Code como análisis técnico de factibilidad. No constituye una decisión final de implementación.*
