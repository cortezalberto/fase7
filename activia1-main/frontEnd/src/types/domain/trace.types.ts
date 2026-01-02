/**
 * Trace Types - Cognitive trace and traceability interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import { TraceLevel } from './enums';

// ==================== COGNITIVE TRACE ====================

/**
 * CognitiveTrace - Traza cognitiva N4 completa
 * Alineado con backend/api/routers/traces.py TraceResponse
 */
export interface CognitiveTrace {
  id: string;
  session_id: string;
  student_id: string;
  activity_id: string;
  trace_level: TraceLevel | string;
  interaction_type: string;
  cognitive_state: string | null;
  cognitive_intent: string | null;
  content: string;
  ai_involvement: number | null;
  // N4 Cognitive fields
  context: Record<string, unknown> | null;
  trace_metadata?: Record<string, unknown>;
  metadata?: Record<string, unknown>;  // Legacy alias
  decision_justification: string | null;
  alternatives_considered: string[] | null;
  strategy_type: string | null;
  // Relationships
  agent_id: string | null;
  parent_trace_id: string | null;
  // Timestamps
  timestamp: string;
  created_at?: string;
}

// ==================== COGNITIVE PATH ====================

/**
 * Punto de evolución de dependencia de IA
 */
export interface AIDependencyPoint {
  timestamp: string;
  ai_involvement: number;
}

/**
 * Fase cognitiva del camino
 */
export interface CognitivePhase {
  phase_name: string;
  start_time: string;
  end_time: string | null;
  duration_minutes: number | null;
  interactions_count: number;
  ai_involvement_avg: number;
  risks_detected: string[];
  key_decisions: string[];
}

/**
 * Transición entre fases cognitivas
 */
export interface CognitiveTransition {
  from_phase: string;
  to_phase: string;
  timestamp: string;
  trigger: string | null;
}

/**
 * Resumen del camino cognitivo
 */
export interface CognitivePathSummary {
  total_interactions: number;
  total_duration_minutes: number;
  blocked_interactions: number;
  ai_dependency_average: number;
  strategy_changes: number;
  risks_total: number;
  risks_by_level: Record<string, number>;
}

/**
 * Camino cognitivo reconstructivo completo
 */
export interface CognitivePath {
  session_id: string;
  student_id: string;
  activity_id: string;
  start_time: string;
  end_time: string | null;
  summary: CognitivePathSummary;
  phases: CognitivePhase[];
  transitions: CognitiveTransition[];
  ai_dependency_evolution: AIDependencyPoint[];
  strategy_changes: string[];
}

// ==================== TRACEABILITY ====================

export interface TraceNode {
  id: string;
  level: 'N1' | 'N2' | 'N3' | 'N4';
  timestamp: string;
  data: unknown;
  metadata: {
    processing_time_ms?: number;
    tokens_used?: number;
    model?: string;
    transformations?: string[];
  };
}

export interface Trace {
  session_id: string;
  interaction_id: string;
  nodes: TraceNode[];
  total_latency_ms: number;
  total_tokens: number;
}
