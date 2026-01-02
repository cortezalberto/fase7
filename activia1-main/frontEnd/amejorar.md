# Propuesta de Mejoras del Frontend para la Arquitectura Multi-Agente Active-IA

## Documento de Especificacion Tecnica

**Version**: 1.0
**Fecha**: Enero 2026
**Referencia**: `backend/ImplementacionAgentes.md`

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Analisis del Impacto en el Frontend](#2-analisis-del-impacto-en-el-frontend)
3. [Nuevos Tipos TypeScript](#3-nuevos-tipos-typescript)
4. [Nuevos Servicios de API](#4-nuevos-servicios-de-api)
5. [Modificaciones a Componentes Existentes](#5-modificaciones-a-componentes-existentes)
6. [Nuevos Componentes](#6-nuevos-componentes)
7. [Nuevos Hooks Personalizados](#7-nuevos-hooks-personalizados)
8. [Modificaciones al Store de Zustand](#8-modificaciones-al-store-de-zustand)
9. [Integracion con el Flujo de Interacciones](#9-integracion-con-el-flujo-de-interacciones)
10. [Visualizacion de Trazabilidad Extendida](#10-visualizacion-de-trazabilidad-extendida)
11. [Panel del Docente - Nuevas Funcionalidades](#11-panel-del-docente---nuevas-funcionalidades)
12. [Feature Flags y Configuracion](#12-feature-flags-y-configuracion)
13. [Plan de Implementacion](#13-plan-de-implementacion)
14. [Consideraciones de UX](#14-consideraciones-de-ux)

---

## 1. Resumen Ejecutivo

La propuesta de arquitectura multi-agente Active-IA introduce cambios significativos en el backend que requieren adaptaciones correspondientes en el frontend. Este documento detalla las modificaciones necesarias para que la interfaz de usuario refleje y aproveche las nuevas capacidades del sistema.

### 1.1 Contexto de la Propuesta Backend

El backend evolucionara de una arquitectura donde el `AIGateway` coordina directamente con agentes individuales, hacia un modelo de **seis agentes especializados** donde cada uno mitiga un riesgo pedagogico especifico:

| Agente | Rol | Impacto en Frontend |
|--------|-----|---------------------|
| **CRPE/Gatekeeper** | Clasificacion de intencion y ruteo | Recibir decisiones de ruteo, mostrar bloqueos pedagogicos |
| **Knowledge-Retrieval (RAG)** | Contexto de conocimiento autorizado | Mostrar fuentes citadas, indicador de confianza RAG |
| **Fallback Pedagogico** | Respuestas generales desacopladas | UI diferenciada para contenido no-evaluable |
| **Scaffolding Agent** | Andamiaje progresivo personalizado | Visualizacion de nivel de ayuda, progresion |
| **Safety & Governance** | Validacion y compliance | Alertas de compliance, warnings visuales |
| **TC-N4** | Trazabilidad cognitiva extendida | Nuevos campos en visualizacion de trazas |

### 1.2 Principios de Diseno para el Frontend

Las modificaciones al frontend deben adherir a los siguientes principios:

**Transparencia Pedagogica**: El estudiante debe comprender por que el sistema responde de cierta manera. Si el Gatekeeper bloquea una solicitud, la razon debe ser clara y educativa. Si el RAG cita fuentes, estas deben ser visibles.

**Progresion Visible**: El nivel de andamiaje actual y la razon por la cual se incremento o redujo deben ser accesibles para el estudiante, fomentando la metacognicion.

**Distincion de Contenido**: Las respuestas del Fallback Pedagogico, que no cuentan para evaluacion, deben diferenciarse visualmente de las respuestas basadas en conocimiento autorizado.

**Continuidad de Experiencia**: Los cambios deben implementarse de forma gradual mediante feature flags, permitiendo que usuarios existentes continuen sin interrupciones mientras se habilitan nuevas funcionalidades.

---

## 2. Analisis del Impacto en el Frontend

### 2.1 Componentes Afectados

La implementacion de la arquitectura multi-agente impacta directamente a los siguientes modulos del frontend:

**Modulo Tutor (`features/tutor/`)**:
El chat con T-IA-Cog ahora recibira respuestas enriquecidas con metadatos de ruteo, fuentes RAG, nivel de scaffolding, y potenciales warnings de governance. Los componentes `ChatMessageBubble` y `TutorHeader` requieren modificaciones para mostrar esta informacion adicional.

**Modulo Training (`features/training/`)**:
El Entrenador Digital interactua con el ScaffoldingAgent para determinar el nivel de pistas. El componente `HintV2Display` debe mostrar no solo la pista sino la justificacion pedagogica del nivel actual y el progreso hacia niveles superiores.

**Modulo Traceability (`features/traceability/`)**:
La visualizacion de trazabilidad N4 debe extenderse para incluir nuevos campos: fuentes RAG, decisiones de ruteo del Gatekeeper, y decisiones del ScaffoldingAgent.

**Panel del Docente (`pages/Teacher*`)**:
Los docentes necesitan visibilidad sobre las decisiones de los nuevos agentes: cuantas solicitudes fueron bloqueadas por el Gatekeeper, que porcentaje de respuestas usaron Fallback Pedagogico, y como progresan los estudiantes a traves de los niveles de scaffolding.

### 2.2 Nuevos Flujos de Datos

El frontend debe consumir nuevos endpoints y estructuras de respuesta:

```
Flujo Actual:
Usuario -> /interactions -> AIGateway -> TutorAgent -> Respuesta

Flujo Propuesto:
Usuario -> /interactions -> Gatekeeper -> (RAG | Fallback) -> TutorAgent -> Scaffolding -> Respuesta
                              |                                    |              |
                              v                                    v              v
                        routing_decision                     rag_sources    help_level
                        cognitive_intent                     confidence     justification
                        risk_level                           is_evaluable
```

Cada interaccion ahora incluye metadatos adicionales que el frontend debe procesar y visualizar.

---

## 3. Nuevos Tipos TypeScript

### 3.1 Ubicacion

Los nuevos tipos se agregaran en `src/types/domain/` siguiendo la estructura modular existente.

### 3.2 Archivo: `gatekeeper.types.ts`

```typescript
/**
 * Tipos relacionados con el CRPE/Gatekeeper Cognitivo
 *
 * El Gatekeeper es el punto de entrada del sistema que clasifica
 * la intencion cognitiva del estudiante y determina la ruta pedagogica.
 */

/**
 * Intencion cognitiva detectada en el mensaje del estudiante
 */
export enum CognitiveIntent {
  /** Exploracion conceptual sin presion de resolver */
  EXPLORATION = 'EXPLORATION',
  /** Solicitud legitima de ayuda para entender */
  HELP = 'HELP',
  /** Intento de obtener la solucion directa */
  SOLUTION = 'SOLUTION',
  /** Validacion de una respuesta o enfoque */
  VALIDATE = 'VALIDATE',
  /** Estado de frustracion que puede requerir intervencion */
  FRUSTRATION = 'FRUSTRATION',
}

/**
 * Decision de ruteo tomada por el Gatekeeper
 */
export enum RoutingDecision {
  /** Continuar al tutor normalmente */
  TUTOR = 'TUTOR',
  /** Usar Fallback Pedagogico (conocimiento insuficiente) */
  FALLBACK = 'FALLBACK',
  /** Bloquear la solicitud (riesgo alto) */
  BLOCK = 'BLOCK',
  /** Escalar a docente (frustracion o caso especial) */
  ESCALATE = 'ESCALATE',
  /** Redirigir a simulador */
  SIMULATOR = 'SIMULATOR',
}

/**
 * Respuesta del Gatekeeper incluida en cada interaccion
 */
export interface GatekeeperDecision {
  cognitive_intent: CognitiveIntent;
  routing_decision: RoutingDecision;
  risk_level: RiskLevel;
  delegation_signals: string[];
  active_restrictions: string[];
  sanitized: boolean;
  pii_detected: boolean;
}
```

### 3.3 Archivo: `rag.types.ts`

```typescript
/**
 * Tipos relacionados con el Knowledge-Retrieval Agent (RAG)
 *
 * El RAG recupera conocimiento autorizado de la catedra para
 * fundamentar las respuestas del tutor.
 */

/**
 * Documento recuperado del corpus de conocimiento
 */
export interface RetrievedDocument {
  /** ID unico del documento en el corpus */
  source_id: string;
  /** Titulo o nombre del documento */
  title: string;
  /** Fragmento relevante del contenido */
  snippet: string;
  /** Unidad tematica a la que pertenece */
  unit: string;
  /** Tipo de contenido */
  content_type: 'theory' | 'example' | 'faq' | 'consigna';
  /** Score de similitud (0-1) */
  score: number;
  /** Dificultad del contenido */
  difficulty: 'basico' | 'intermedio' | 'avanzado';
}

/**
 * Resultado de la consulta RAG incluido en la respuesta
 */
export interface RAGResult {
  /** Documentos recuperados ordenados por relevancia */
  documents: RetrievedDocument[];
  /** Score de confianza agregado */
  confidence_score: number;
  /** IDs de fuentes para trazabilidad */
  source_traceability: string[];
  /** Si el conocimiento recuperado fue suficiente */
  sufficient: boolean;
  /** Si se uso Fallback Pedagogico */
  used_fallback: boolean;
}
```

### 3.4 Archivo: `scaffolding.types.ts`

```typescript
/**
 * Tipos relacionados con el Scaffolding Agent
 *
 * El Scaffolding personaliza el nivel de ayuda basandose
 * en el historial del estudiante.
 */

/**
 * Tipo de ayuda segun el nivel de scaffolding
 */
export type ScaffoldingHelpType =
  | 'muy_abstracto'    // Nivel 1: Solo preguntas orientadoras
  | 'conceptual'       // Nivel 2: Preguntas + nombres de conceptos
  | 'mas_concreto'     // Nivel 3: Preguntas + estrategia alto nivel
  | 'especifico';      // Nivel 4: Preguntas + pseudocodigo abstracto

/**
 * Decision de scaffolding para la interaccion actual
 */
export interface ScaffoldingDecision {
  /** Nivel de ayuda actual (1-4) */
  help_level: 1 | 2 | 3 | 4;
  /** Tipo de ayuda correspondiente al nivel */
  help_type: ScaffoldingHelpType;
  /** Justificacion pedagogica de por que este nivel */
  pedagogical_justification: string;
  /** Si el nivel avanzo respecto a la interaccion anterior */
  level_advanced: boolean;
  /** Razones por las que avanzo el nivel */
  advancement_reasons?: string[];
  /** Intentos fallidos desde la ultima pista */
  attempts_since_last_hint: number;
  /** Tiempo estancado (en segundos) */
  time_stagnated_seconds: number;
}
```

### 3.5 Archivo: `fallback.types.ts`

```typescript
/**
 * Tipos relacionados con el Fallback Pedagogico
 *
 * El Fallback proporciona explicaciones generales cuando
 * el conocimiento local no es suficiente.
 */

/**
 * Respuesta del Fallback Pedagogico
 */
export interface FallbackResponse {
  /** Explicacion conceptual general */
  explanation: string;
  /** Disclaimer sobre el contenido */
  disclaimer: string;
  /** Sugerencias para el estudiante */
  suggestions: string[];
  /** Explicito: este contenido no es evaluable */
  is_evaluable: false;
  /** Referencias externas sugeridas */
  external_references?: string[];
}
```

### 3.6 Modificacion: `interaction.types.ts`

La interfaz `InteractionResponse` existente debe extenderse para incluir los nuevos metadatos:

```typescript
/**
 * Respuesta extendida de interaccion con metadatos multi-agente
 */
export interface InteractionResponseV2 extends InteractionResponse {
  /** Decision del Gatekeeper */
  gatekeeper?: GatekeeperDecision;
  /** Resultado del RAG */
  rag_result?: RAGResult;
  /** Decision de Scaffolding */
  scaffolding?: ScaffoldingDecision;
  /** Respuesta de Fallback (si aplica) */
  fallback?: FallbackResponse;
  /** Warnings de Governance */
  governance_warnings?: string[];
  /** Si la respuesta fue bloqueada */
  was_blocked: boolean;
  /** Razon del bloqueo (si aplica) */
  block_reason?: string;
}
```

### 3.7 Actualizacion del Barrel Export

En `src/types/domain/index.ts`:

```typescript
// ==================== GATEKEEPER ====================
export {
  CognitiveIntent,
  RoutingDecision,
  type GatekeeperDecision,
} from './gatekeeper.types';

// ==================== RAG ====================
export type {
  RetrievedDocument,
  RAGResult,
} from './rag.types';

// ==================== SCAFFOLDING ====================
export type {
  ScaffoldingHelpType,
  ScaffoldingDecision,
} from './scaffolding.types';

// ==================== FALLBACK ====================
export type {
  FallbackResponse,
} from './fallback.types';
```

---

## 4. Nuevos Servicios de API

### 4.1 Archivo: `gatekeeper.service.ts`

```typescript
/**
 * Servicio para interactuar con endpoints del Gatekeeper
 *
 * Proporciona acceso a estadisticas y configuracion del
 * CRPE/Gatekeeper Cognitivo.
 */

import { apiClient } from './client';
import type { GatekeeperDecision, CognitiveIntent, RoutingDecision } from '@/types/domain';

export interface GatekeeperStats {
  total_requests: number;
  routing_distribution: Record<RoutingDecision, number>;
  intent_distribution: Record<CognitiveIntent, number>;
  block_rate: number;
  escalation_rate: number;
  period: 'day' | 'week' | 'month';
}

export interface GatekeeperConfig {
  delegation_signals_threshold: number;
  frustration_keywords_threshold: number;
  allow_escalation: boolean;
  strict_mode: boolean;
}

class GatekeeperService {
  /**
   * Obtiene estadisticas del Gatekeeper para el periodo especificado
   * Solo disponible para docentes
   */
  async getStats(period: 'day' | 'week' | 'month' = 'week'): Promise<GatekeeperStats> {
    const response = await apiClient.get<{ data: GatekeeperStats }>(
      `/gatekeeper/stats?period=${period}`
    );
    return response.data.data;
  }

  /**
   * Obtiene la configuracion actual del Gatekeeper
   * Solo disponible para administradores
   */
  async getConfig(): Promise<GatekeeperConfig> {
    const response = await apiClient.get<{ data: GatekeeperConfig }>(
      '/gatekeeper/config'
    );
    return response.data.data;
  }

  /**
   * Actualiza la configuracion del Gatekeeper
   * Solo disponible para administradores
   */
  async updateConfig(config: Partial<GatekeeperConfig>): Promise<GatekeeperConfig> {
    const response = await apiClient.patch<{ data: GatekeeperConfig }>(
      '/gatekeeper/config',
      config
    );
    return response.data.data;
  }
}

export const gatekeeperService = new GatekeeperService();
```

### 4.2 Archivo: `rag.service.ts`

```typescript
/**
 * Servicio para interactuar con el Knowledge-Retrieval Agent
 *
 * Permite consultar el corpus de conocimiento y gestionar documentos.
 */

import { apiClient } from './client';
import type { RetrievedDocument, RAGResult } from '@/types/domain';

export interface RAGStats {
  total_queries: number;
  avg_confidence: number;
  fallback_rate: number;
  top_sources: Array<{ source_id: string; count: number }>;
  period: 'day' | 'week' | 'month';
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  content: string;
  content_type: 'theory' | 'example' | 'faq' | 'consigna';
  unit: string;
  difficulty: 'basico' | 'intermedio' | 'avanzado';
  created_at: string;
  updated_at: string;
}

class RAGService {
  /**
   * Obtiene estadisticas del RAG
   * Solo disponible para docentes
   */
  async getStats(period: 'day' | 'week' | 'month' = 'week'): Promise<RAGStats> {
    const response = await apiClient.get<{ data: RAGStats }>(
      `/rag/stats?period=${period}`
    );
    return response.data.data;
  }

  /**
   * Lista documentos del corpus de conocimiento
   * Solo disponible para docentes
   */
  async listDocuments(params?: {
    unit?: string;
    content_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<KnowledgeDocument[]> {
    const response = await apiClient.get<{ data: KnowledgeDocument[] }>(
      '/rag/documents',
      { params }
    );
    return response.data.data;
  }

  /**
   * Crea un nuevo documento en el corpus
   * Solo disponible para docentes
   */
  async createDocument(doc: Omit<KnowledgeDocument, 'id' | 'created_at' | 'updated_at'>): Promise<KnowledgeDocument> {
    const response = await apiClient.post<{ data: KnowledgeDocument }>(
      '/rag/documents',
      doc
    );
    return response.data.data;
  }

  /**
   * Ejecuta una consulta de prueba contra el RAG
   * Util para verificar que el contenido se recupera correctamente
   */
  async testQuery(query: string, filters?: {
    unit?: string;
    difficulty?: string;
  }): Promise<RAGResult> {
    const response = await apiClient.post<{ data: RAGResult }>(
      '/rag/test-query',
      { query, filters }
    );
    return response.data.data;
  }
}

export const ragService = new RAGService();
```

### 4.3 Archivo: `scaffolding.service.ts`

```typescript
/**
 * Servicio para interactuar con el Scaffolding Agent
 *
 * Permite consultar el historial de scaffolding de un estudiante
 * y las estadisticas de progresion.
 */

import { apiClient } from './client';
import type { ScaffoldingDecision } from '@/types/domain';

export interface ScaffoldingHistory {
  session_id: string;
  activity_id: string;
  decisions: Array<{
    timestamp: string;
    level: 1 | 2 | 3 | 4;
    justification: string;
    triggered_by: 'attempts' | 'time' | 'request';
  }>;
  final_level: number;
  total_progressions: number;
}

export interface ScaffoldingStats {
  avg_starting_level: number;
  avg_final_level: number;
  progression_rate: number;
  students_at_level: Record<1 | 2 | 3 | 4, number>;
  period: 'day' | 'week' | 'month';
}

class ScaffoldingService {
  /**
   * Obtiene el historial de scaffolding de una sesion
   */
  async getSessionHistory(sessionId: string): Promise<ScaffoldingHistory> {
    const response = await apiClient.get<{ data: ScaffoldingHistory }>(
      `/scaffolding/session/${sessionId}/history`
    );
    return response.data.data;
  }

  /**
   * Obtiene estadisticas de scaffolding
   * Solo disponible para docentes
   */
  async getStats(period: 'day' | 'week' | 'month' = 'week'): Promise<ScaffoldingStats> {
    const response = await apiClient.get<{ data: ScaffoldingStats }>(
      `/scaffolding/stats?period=${period}`
    );
    return response.data.data;
  }

  /**
   * Obtiene el nivel de scaffolding actual para un estudiante en una actividad
   */
  async getCurrentLevel(studentId: string, activityId: string): Promise<ScaffoldingDecision> {
    const response = await apiClient.get<{ data: ScaffoldingDecision }>(
      `/scaffolding/student/${studentId}/activity/${activityId}/current`
    );
    return response.data.data;
  }
}

export const scaffoldingService = new ScaffoldingService();
```

### 4.4 Actualizacion de `index.ts`

```typescript
// Nuevos servicios
export { gatekeeperService } from './gatekeeper.service';
export type { GatekeeperStats, GatekeeperConfig } from './gatekeeper.service';

export { ragService } from './rag.service';
export type { RAGStats, KnowledgeDocument } from './rag.service';

export { scaffoldingService } from './scaffolding.service';
export type { ScaffoldingHistory, ScaffoldingStats } from './scaffolding.service';
```

---

## 5. Modificaciones a Componentes Existentes

### 5.1 `ChatMessageBubble.tsx` (features/tutor/components/)

El componente de burbuja de mensaje debe extenderse para mostrar informacion de los nuevos agentes:

**Cambios Requeridos**:

1. **Indicador de Fuentes RAG**: Cuando la respuesta incluye `rag_result`, mostrar un boton "Ver fuentes" que expande una lista de documentos citados.

2. **Badge de Nivel de Scaffolding**: Mostrar el nivel actual (1-4) con un icono que indica si avanzo.

3. **Alerta de Fallback**: Si `fallback` esta presente, renderizar la burbuja con estilo diferenciado (borde amarillo, icono de advertencia) y mostrar el disclaimer.

4. **Warning de Governance**: Si hay `governance_warnings`, mostrar un banner sutil encima del mensaje.

```tsx
interface ChatMessageBubbleProps {
  message: ChatMessage;
  // Nuevos props para metadatos multi-agente
  ragResult?: RAGResult;
  scaffolding?: ScaffoldingDecision;
  fallback?: FallbackResponse;
  governanceWarnings?: string[];
}

function ChatMessageBubble({
  message,
  ragResult,
  scaffolding,
  fallback,
  governanceWarnings,
}: ChatMessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);

  const isFallbackResponse = !!fallback;

  return (
    <div className={cn(
      "rounded-lg p-4",
      message.role === 'assistant' && "bg-[var(--bg-secondary)]",
      isFallbackResponse && "border-l-4 border-yellow-500"
    )}>
      {/* Governance Warnings */}
      {governanceWarnings && governanceWarnings.length > 0 && (
        <GovernanceWarningBanner warnings={governanceWarnings} />
      )}

      {/* Scaffolding Level Badge */}
      {scaffolding && (
        <ScaffoldingLevelBadge
          level={scaffolding.help_level}
          advanced={scaffolding.level_advanced}
          justification={scaffolding.pedagogical_justification}
        />
      )}

      {/* Message Content */}
      <div className="prose prose-invert">
        <ReactMarkdown>{message.content}</ReactMarkdown>
      </div>

      {/* Fallback Disclaimer */}
      {fallback && (
        <FallbackDisclaimer
          disclaimer={fallback.disclaimer}
          suggestions={fallback.suggestions}
        />
      )}

      {/* RAG Sources */}
      {ragResult && ragResult.documents.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setShowSources(!showSources)}
            className="text-sm text-[var(--accent-primary)] hover:underline flex items-center gap-1"
          >
            <BookOpen className="w-4 h-4" />
            {showSources ? 'Ocultar' : 'Ver'} {ragResult.documents.length} fuentes
            ({Math.round(ragResult.confidence_score * 100)}% confianza)
          </button>
          {showSources && (
            <RAGSourcesList documents={ragResult.documents} />
          )}
        </div>
      )}
    </div>
  );
}
```

### 5.2 `HintV2Display.tsx` (features/training/components/)

El componente de pistas V2 debe mostrar la justificacion pedagogica del nivel de scaffolding:

**Cambios Requeridos**:

1. **Barra de Progreso de Nivel**: Visualizar el nivel actual (1-4) como barra de progreso.

2. **Tooltip de Justificacion**: Al hacer hover sobre el nivel, mostrar la `pedagogical_justification`.

3. **Indicador de Avance**: Si `level_advanced` es true, mostrar animacion o badge que indica "Nivel aumentado".

4. **Metricas de Estancamiento**: Mostrar sutilmente cuantos intentos o tiempo lleva en el nivel actual.

```tsx
interface HintV2DisplayProps {
  hint: PistaV2Response;
  scaffolding?: ScaffoldingDecision;
  onRequestNextLevel?: () => void;
}

function HintV2Display({ hint, scaffolding, onRequestNextLevel }: HintV2DisplayProps) {
  return (
    <div className="bg-[var(--bg-tertiary)] rounded-lg p-4">
      {/* Scaffolding Progress */}
      {scaffolding && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-[var(--text-secondary)]">
              Nivel de ayuda: {scaffolding.help_type}
            </span>
            {scaffolding.level_advanced && (
              <span className="text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded">
                Nivel aumentado
              </span>
            )}
          </div>

          <ScaffoldingProgressBar
            level={scaffolding.help_level}
            justification={scaffolding.pedagogical_justification}
          />

          {scaffolding.attempts_since_last_hint > 0 && (
            <p className="text-xs text-[var(--text-muted)] mt-1">
              {scaffolding.attempts_since_last_hint} intentos desde la ultima pista
            </p>
          )}
        </div>
      )}

      {/* Hint Content */}
      <div className="prose prose-invert">
        <ReactMarkdown>{hint.pista}</ReactMarkdown>
      </div>

      {/* Follow-up Question */}
      {hint.pregunta_seguimiento && (
        <div className="mt-4 p-3 bg-[var(--bg-primary)] rounded border border-[var(--border-color)]">
          <p className="text-sm font-medium">Pregunta para reflexionar:</p>
          <p className="text-[var(--text-secondary)]">{hint.pregunta_seguimiento}</p>
        </div>
      )}
    </div>
  );
}
```

### 5.3 `TraceNodeCard.tsx` (features/traceability/components/)

El componente de nodo de traza debe extenderse para mostrar los nuevos campos:

**Cambios Requeridos**:

1. **Seccion RAG**: Si la traza incluye `rag_sources`, mostrar lista de IDs de documentos citados.

2. **Seccion Gatekeeper**: Si incluye `gatekeeper_decision`, mostrar intencion cognitiva detectada y decision de ruteo.

3. **Seccion Scaffolding**: Si incluye `scaffolding_level`, mostrar el nivel aplicado.

```tsx
interface TraceNodeCardProps {
  trace: CognitiveTrace;
  // Campos extendidos
  ragSources?: string[];
  gatekeeperDecision?: GatekeeperDecision;
  scaffoldingLevel?: number;
}
```

---

## 6. Nuevos Componentes

### 6.1 `RAGSourcesList.tsx`

Componente para mostrar la lista de documentos recuperados por el RAG:

```tsx
/**
 * Lista expandible de fuentes RAG citadas en una respuesta
 *
 * Muestra titulo, tipo de contenido, unidad y score de similitud
 * para cada documento recuperado.
 */

interface RAGSourcesListProps {
  documents: RetrievedDocument[];
  maxVisible?: number;
}

function RAGSourcesList({ documents, maxVisible = 3 }: RAGSourcesListProps) {
  const [expanded, setExpanded] = useState(false);
  const visibleDocs = expanded ? documents : documents.slice(0, maxVisible);

  return (
    <div className="mt-2 space-y-2">
      {visibleDocs.map((doc) => (
        <div
          key={doc.source_id}
          className="flex items-start gap-3 p-2 bg-[var(--bg-primary)] rounded text-sm"
        >
          <ContentTypeIcon type={doc.content_type} />
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{doc.title}</p>
            <p className="text-[var(--text-muted)] text-xs">
              {doc.unit} · {doc.difficulty} · {Math.round(doc.score * 100)}% relevancia
            </p>
            {doc.snippet && (
              <p className="text-[var(--text-secondary)] text-xs mt-1 line-clamp-2">
                "{doc.snippet}"
              </p>
            )}
          </div>
        </div>
      ))}

      {documents.length > maxVisible && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-[var(--accent-primary)] hover:underline"
        >
          {expanded ? 'Ver menos' : `Ver ${documents.length - maxVisible} mas`}
        </button>
      )}
    </div>
  );
}
```

### 6.2 `ScaffoldingProgressBar.tsx`

Visualizacion del nivel de scaffolding actual:

```tsx
/**
 * Barra de progreso visual para niveles de scaffolding
 *
 * Muestra los 4 niveles con el actual resaltado y tooltip
 * de justificacion pedagogica.
 */

interface ScaffoldingProgressBarProps {
  level: 1 | 2 | 3 | 4;
  justification: string;
}

const LEVEL_LABELS = {
  1: 'Abstracto',
  2: 'Conceptual',
  3: 'Concreto',
  4: 'Especifico',
};

function ScaffoldingProgressBar({ level, justification }: ScaffoldingProgressBarProps) {
  return (
    <Tooltip content={justification}>
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((l) => (
          <div
            key={l}
            className={cn(
              "flex-1 h-2 rounded-full transition-colors",
              l <= level
                ? "bg-gradient-to-r from-indigo-500 to-purple-500"
                : "bg-[var(--bg-tertiary)]"
            )}
          />
        ))}
      </div>
      <div className="flex justify-between mt-1">
        {[1, 2, 3, 4].map((l) => (
          <span
            key={l}
            className={cn(
              "text-xs",
              l === level ? "text-[var(--accent-primary)]" : "text-[var(--text-muted)]"
            )}
          >
            {LEVEL_LABELS[l as 1 | 2 | 3 | 4]}
          </span>
        ))}
      </div>
    </Tooltip>
  );
}
```

### 6.3 `FallbackDisclaimer.tsx`

Banner de advertencia para respuestas de Fallback Pedagogico:

```tsx
/**
 * Disclaimer visual para respuestas de Fallback Pedagogico
 *
 * Indica claramente que el contenido es general y no evaluable.
 */

interface FallbackDisclaimerProps {
  disclaimer: string;
  suggestions: string[];
}

function FallbackDisclaimer({ disclaimer, suggestions }: FallbackDisclaimerProps) {
  return (
    <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
      <div className="flex items-start gap-2">
        <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm text-yellow-200">{disclaimer}</p>
          {suggestions.length > 0 && (
            <ul className="mt-2 space-y-1">
              {suggestions.map((suggestion, idx) => (
                <li key={idx} className="text-xs text-[var(--text-muted)] flex items-center gap-1">
                  <span>•</span> {suggestion}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
```

### 6.4 `GovernanceWarningBanner.tsx`

Banner para warnings de governance:

```tsx
/**
 * Banner para mostrar warnings del Governance Agent
 *
 * Aparece encima del mensaje cuando hay advertencias de compliance.
 */

interface GovernanceWarningBannerProps {
  warnings: string[];
}

function GovernanceWarningBanner({ warnings }: GovernanceWarningBannerProps) {
  if (warnings.length === 0) return null;

  return (
    <div className="mb-3 p-2 bg-orange-500/10 border-l-2 border-orange-500 rounded-r">
      <div className="flex items-center gap-2 text-orange-400">
        <Shield className="w-4 h-4" />
        <span className="text-xs font-medium">Advertencia de Gobernanza</span>
      </div>
      <ul className="mt-1 space-y-0.5">
        {warnings.map((warning, idx) => (
          <li key={idx} className="text-xs text-[var(--text-secondary)]">
            {warning}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### 6.5 `BlockedRequestCard.tsx`

Componente para mostrar cuando el Gatekeeper bloquea una solicitud:

```tsx
/**
 * Tarjeta informativa cuando una solicitud es bloqueada
 *
 * Explica la razon pedagogica del bloqueo y sugiere alternativas.
 */

interface BlockedRequestCardProps {
  reason: string;
  cognitiveIntent: CognitiveIntent;
  suggestions?: string[];
  onTryAgain?: () => void;
}

function BlockedRequestCard({
  reason,
  cognitiveIntent,
  suggestions,
  onTryAgain,
}: BlockedRequestCardProps) {
  return (
    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
          <XCircle className="w-5 h-5 text-red-400" />
        </div>
        <div className="flex-1">
          <h4 className="font-medium text-red-300">
            Solicitud no procesada
          </h4>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {reason}
          </p>

          {cognitiveIntent === CognitiveIntent.SOLUTION && (
            <p className="text-xs text-[var(--text-muted)] mt-2">
              Detectamos que estas buscando la solucion directa. Nuestro objetivo
              es ayudarte a aprender, no darte respuestas completas.
            </p>
          )}

          {suggestions && suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-medium text-[var(--text-secondary)]">
                Intenta reformular tu pregunta:
              </p>
              <ul className="mt-1 space-y-1">
                {suggestions.map((s, idx) => (
                  <li key={idx} className="text-xs text-[var(--text-muted)]">
                    • {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {onTryAgain && (
            <button
              onClick={onTryAgain}
              className="mt-4 text-sm text-[var(--accent-primary)] hover:underline"
            >
              Intentar de nuevo
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
```

---

## 7. Nuevos Hooks Personalizados

### 7.1 `useGatekeeperStats.ts`

Hook para obtener estadisticas del Gatekeeper (para docentes):

```typescript
/**
 * Hook para consultar estadisticas del Gatekeeper
 *
 * Solo disponible para usuarios con rol docente.
 */

import { useState, useEffect, useCallback } from 'react';
import { gatekeeperService, GatekeeperStats } from '@/services/api';

interface UseGatekeeperStatsReturn {
  stats: GatekeeperStats | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useGatekeeperStats(
  period: 'day' | 'week' | 'month' = 'week'
): UseGatekeeperStatsReturn {
  const [stats, setStats] = useState<GatekeeperStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await gatekeeperService.getStats(period);
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Error fetching stats'));
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}
```

### 7.2 `useScaffoldingHistory.ts`

Hook para obtener el historial de scaffolding de una sesion:

```typescript
/**
 * Hook para consultar el historial de scaffolding de una sesion
 *
 * Muestra como fue progresando el nivel de ayuda durante la sesion.
 */

import { useState, useEffect, useCallback } from 'react';
import { scaffoldingService, ScaffoldingHistory } from '@/services/api';

interface UseScaffoldingHistoryReturn {
  history: ScaffoldingHistory | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useScaffoldingHistory(sessionId: string): UseScaffoldingHistoryReturn {
  const [history, setHistory] = useState<ScaffoldingHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchHistory = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);
    try {
      const data = await scaffoldingService.getSessionHistory(sessionId);
      setHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Error fetching history'));
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  return { history, loading, error, refetch: fetchHistory };
}
```

### 7.3 `useRAGDocuments.ts`

Hook para gestionar documentos del corpus RAG (para docentes):

```typescript
/**
 * Hook para gestionar documentos del corpus de conocimiento RAG
 *
 * Permite listar, crear y buscar documentos.
 * Solo disponible para docentes.
 */

import { useState, useEffect, useCallback } from 'react';
import { ragService, KnowledgeDocument } from '@/services/api';

interface UseRAGDocumentsParams {
  unit?: string;
  content_type?: string;
  limit?: number;
}

interface UseRAGDocumentsReturn {
  documents: KnowledgeDocument[];
  loading: boolean;
  error: Error | null;
  createDocument: (doc: Omit<KnowledgeDocument, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  refetch: () => Promise<void>;
}

export function useRAGDocuments(params?: UseRAGDocumentsParams): UseRAGDocumentsReturn {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ragService.listDocuments(params);
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Error fetching documents'));
    } finally {
      setLoading(false);
    }
  }, [params?.unit, params?.content_type, params?.limit]);

  const createDocument = useCallback(async (
    doc: Omit<KnowledgeDocument, 'id' | 'created_at' | 'updated_at'>
  ) => {
    const newDoc = await ragService.createDocument(doc);
    setDocuments(prev => [newDoc, ...prev]);
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  return { documents, loading, error, createDocument, refetch: fetchDocuments };
}
```

---

## 8. Modificaciones al Store de Zustand

### 8.1 Nuevo Store: `agentMetadataStore.ts`

Store para mantener metadatos de agentes durante una sesion:

```typescript
/**
 * Store para metadatos de agentes multi-agente
 *
 * Mantiene el estado de scaffolding, decisiones de gatekeeper,
 * y resultados RAG de la sesion actual.
 */

import { create } from 'zustand';
import type {
  ScaffoldingDecision,
  GatekeeperDecision,
  RAGResult,
} from '@/types/domain';

interface AgentMetadataState {
  // Scaffolding
  currentScaffoldingLevel: number;
  scaffoldingHistory: ScaffoldingDecision[];

  // Gatekeeper
  lastGatekeeperDecision: GatekeeperDecision | null;
  blockedCount: number;

  // RAG
  lastRAGResult: RAGResult | null;
  fallbackCount: number;

  // Actions
  updateScaffolding: (decision: ScaffoldingDecision) => void;
  updateGatekeeper: (decision: GatekeeperDecision) => void;
  updateRAG: (result: RAGResult) => void;
  incrementBlocked: () => void;
  incrementFallback: () => void;
  reset: () => void;
}

const initialState = {
  currentScaffoldingLevel: 1,
  scaffoldingHistory: [],
  lastGatekeeperDecision: null,
  blockedCount: 0,
  lastRAGResult: null,
  fallbackCount: 0,
};

export const useAgentMetadataStore = create<AgentMetadataState>((set) => ({
  ...initialState,

  updateScaffolding: (decision) => set((state) => ({
    currentScaffoldingLevel: decision.help_level,
    scaffoldingHistory: [...state.scaffoldingHistory, decision],
  })),

  updateGatekeeper: (decision) => set({
    lastGatekeeperDecision: decision,
  }),

  updateRAG: (result) => set({
    lastRAGResult: result,
  }),

  incrementBlocked: () => set((state) => ({
    blockedCount: state.blockedCount + 1,
  })),

  incrementFallback: () => set((state) => ({
    fallbackCount: state.fallbackCount + 1,
  })),

  reset: () => set(initialState),
}));
```

### 8.2 Extension de `sessionStore.ts`

Agregar campos relacionados con los nuevos agentes:

```typescript
// Agregar a la interfaz ActiveSession existente
interface ActiveSession {
  // ... campos existentes ...

  // Nuevos campos multi-agente
  scaffoldingLevel?: number;
  ragConfidence?: number;
  wasBlockedCount?: number;
  usedFallbackCount?: number;
}
```

---

## 9. Integracion con el Flujo de Interacciones

### 9.1 Modificacion de `useTutorSession.ts`

El hook principal de sesion de tutoria debe procesar los nuevos metadatos:

```typescript
// Agregar al procesamiento de respuesta de interaccion
const processInteractionResponse = useCallback((response: InteractionResponseV2) => {
  // Procesar Gatekeeper
  if (response.gatekeeper) {
    agentMetadataStore.updateGatekeeper(response.gatekeeper);

    if (response.was_blocked) {
      agentMetadataStore.incrementBlocked();
      setBlockedMessage({
        reason: response.block_reason || 'Solicitud bloqueada',
        intent: response.gatekeeper.cognitive_intent,
      });
      return; // No continuar procesando
    }
  }

  // Procesar RAG
  if (response.rag_result) {
    agentMetadataStore.updateRAG(response.rag_result);

    if (response.rag_result.used_fallback) {
      agentMetadataStore.incrementFallback();
    }
  }

  // Procesar Scaffolding
  if (response.scaffolding) {
    agentMetadataStore.updateScaffolding(response.scaffolding);
  }

  // Agregar mensaje con metadatos
  addMessage({
    ...response,
    ragResult: response.rag_result,
    scaffolding: response.scaffolding,
    fallback: response.fallback,
    governanceWarnings: response.governance_warnings,
  });
}, []);
```

### 9.2 Manejo de Bloqueos

Cuando el Gatekeeper bloquea una solicitud, la UI debe mostrar el componente `BlockedRequestCard` en lugar de una respuesta normal:

```typescript
// En TutorPage.tsx o TutorChat.tsx
{blockedMessage ? (
  <BlockedRequestCard
    reason={blockedMessage.reason}
    cognitiveIntent={blockedMessage.intent}
    suggestions={getSuggestionsForIntent(blockedMessage.intent)}
    onTryAgain={() => setBlockedMessage(null)}
  />
) : (
  <ChatMessageBubble
    message={latestMessage}
    ragResult={latestMessage.ragResult}
    scaffolding={latestMessage.scaffolding}
    fallback={latestMessage.fallback}
    governanceWarnings={latestMessage.governanceWarnings}
  />
)}
```

---

## 10. Visualizacion de Trazabilidad Extendida

### 10.1 Nuevos Campos en Trazas

La visualizacion de trazabilidad N4 debe extenderse para mostrar:

| Campo | Visualizacion |
|-------|---------------|
| `rag_sources` | Lista de IDs de documentos citados |
| `rag_confidence` | Porcentaje de confianza |
| `gatekeeper_intent` | Badge con intencion detectada |
| `gatekeeper_routing` | Flecha indicando ruta tomada |
| `scaffolding_level` | Numero con barra de progreso |
| `scaffolding_justification` | Tooltip con explicacion |
| `used_fallback` | Icono de advertencia |

### 10.2 Diagrama de Flujo Visual

Agregar un componente que muestre visualmente el flujo de la solicitud a traves de los agentes:

```
[Estudiante] -> [Gatekeeper] -> [RAG] -> [Tutor] -> [Safety] -> [Scaffolding] -> [Respuesta]
                    |             |         |          |             |
                  HELP         0.85      socratic     OK           L2
```

---

## 11. Panel del Docente - Nuevas Funcionalidades

### 11.1 Dashboard de Agentes

Nueva pagina o seccion en el panel docente para monitorear los agentes:

**Metricas del Gatekeeper**:
- Distribucion de intenciones cognitivas detectadas
- Tasa de bloqueo por tipo de intencion
- Tendencia de riesgo en el tiempo

**Metricas del RAG**:
- Confianza promedio de respuestas
- Documentos mas citados
- Tasa de uso de Fallback

**Metricas de Scaffolding**:
- Nivel promedio de ayuda por actividad
- Tasa de progresion de niveles
- Estudiantes estancados en nivel 4

### 11.2 Gestion de Corpus RAG

Nueva pagina para que docentes gestionen el corpus de conocimiento:

- Listar documentos existentes por unidad/tipo
- Crear nuevos documentos
- Probar consultas contra el RAG
- Ver estadisticas de uso de cada documento

---

## 12. Feature Flags y Configuracion

### 12.1 Variables de Entorno

Agregar a `.env`:

```env
# Feature flags para nueva arquitectura multi-agente
VITE_ENABLE_GATEKEEPER_UI=true
VITE_ENABLE_RAG_SOURCES=true
VITE_ENABLE_SCAFFOLDING_PROGRESS=true
VITE_ENABLE_FALLBACK_DISCLAIMER=true
VITE_ENABLE_GOVERNANCE_WARNINGS=true

# Feature flags para panel docente
VITE_ENABLE_AGENT_DASHBOARD=true
VITE_ENABLE_RAG_MANAGEMENT=true
```

### 12.2 Hook de Feature Flags

```typescript
/**
 * Hook para verificar feature flags de agentes multi-agente
 */

export function useAgentFeatures() {
  return {
    gatekeeperUI: import.meta.env.VITE_ENABLE_GATEKEEPER_UI === 'true',
    ragSources: import.meta.env.VITE_ENABLE_RAG_SOURCES === 'true',
    scaffoldingProgress: import.meta.env.VITE_ENABLE_SCAFFOLDING_PROGRESS === 'true',
    fallbackDisclaimer: import.meta.env.VITE_ENABLE_FALLBACK_DISCLAIMER === 'true',
    governanceWarnings: import.meta.env.VITE_ENABLE_GOVERNANCE_WARNINGS === 'true',
    agentDashboard: import.meta.env.VITE_ENABLE_AGENT_DASHBOARD === 'true',
    ragManagement: import.meta.env.VITE_ENABLE_RAG_MANAGEMENT === 'true',
  };
}
```

---

## 13. Plan de Implementacion

### 13.1 Fase 1: Tipos y Servicios (1 semana)

1. Crear archivos de tipos en `types/domain/`
2. Crear servicios en `services/api/`
3. Actualizar barrel exports
4. Tests unitarios para servicios

### 13.2 Fase 2: Componentes Base (1 semana)

1. Implementar `RAGSourcesList`
2. Implementar `ScaffoldingProgressBar`
3. Implementar `FallbackDisclaimer`
4. Implementar `GovernanceWarningBanner`
5. Implementar `BlockedRequestCard`

### 13.3 Fase 3: Integracion en Tutor (1 semana)

1. Modificar `ChatMessageBubble`
2. Modificar `useTutorSession`
3. Crear `agentMetadataStore`
4. Integrar feature flags

### 13.4 Fase 4: Integracion en Training (1 semana)

1. Modificar `HintV2Display`
2. Modificar `useTrainingSession`
3. Agregar hooks de scaffolding

### 13.5 Fase 5: Panel Docente (2 semanas)

1. Nueva pagina `AgentDashboardPage`
2. Nueva pagina `RAGManagementPage`
3. Integrar graficos y metricas
4. Testing E2E

---

## 14. Consideraciones de UX

### 14.1 No Abrumar al Usuario

Los nuevos metadatos de agentes contienen mucha informacion, pero no toda debe mostrarse siempre:

- **Fuentes RAG**: Colapsadas por defecto, expandibles con click
- **Scaffolding**: Solo mostrar el nivel, justificacion en tooltip
- **Fallback**: Disclaimer visible pero no invasivo
- **Governance**: Solo mostrar si hay warnings

### 14.2 Educacion Progresiva

Introducir tooltips y onboarding que expliquen:
- Que significa el nivel de scaffolding
- Por que algunas respuestas tienen disclaimer
- Como interpretar las fuentes citadas

### 14.3 Accesibilidad

Todos los nuevos componentes deben:
- Tener `aria-label` descriptivos
- Ser navegables por teclado
- Tener contraste adecuado para los colores de warning/error

---

## Conclusion

La adopcion de la arquitectura multi-agente Active-IA en el frontend representa una evolucion significativa que mejorara la experiencia educativa de los estudiantes al hacerla mas transparente y personalizada. Las modificaciones propuestas mantienen compatibilidad con el sistema actual mediante feature flags, permitiendo una migracion gradual y segura.

Los principales beneficios para el usuario final seran:
1. **Transparencia**: Entender por que el sistema responde de cierta manera
2. **Progresion visible**: Ver como avanza su nivel de ayuda
3. **Fuentes verificables**: Acceder a los documentos que fundamentan las respuestas
4. **Feedback educativo**: Incluso cuando una solicitud es bloqueada, recibir orientacion constructiva

---

*Documento generado: Enero 2026*
*Version: 1.0*
*Referencia: backend/ImplementacionAgentes.md*
