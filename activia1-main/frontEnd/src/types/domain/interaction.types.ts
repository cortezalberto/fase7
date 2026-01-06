/**
 * Interaction Types - Interaction-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 * Cortez92: Fixed ChatMessage.timestamp type to string for consistency
 */

import { CognitiveIntent, MessageStatus } from './enums';

// ==================== INTERACTION ====================

/**
 * InteractionCreate - Legacy alias for InteractionRequest
 * @deprecated Use InteractionRequest instead
 */
export interface InteractionCreate {
  session_id: string;
  prompt: string;
  context?: Record<string, unknown>;
  cognitive_intent?: CognitiveIntent;
}

export interface InteractionRequest {
  session_id: string;
  prompt: string;
  context?: Record<string, unknown>;
  cognitive_intent?: CognitiveIntent;
}

export interface InteractionResponse {
  /**
   * @deprecated Use interaction_id instead - will be removed in v2.0
   */
  id?: string;
  interaction_id: string;
  session_id: string;
  response: string;
  agent_used: string;
  cognitive_state_detected: string;
  ai_involvement: number;
  blocked: boolean;
  block_reason: string | null;
  trace_id: string;
  risks_detected: string[];
  timestamp: string;
  tokens_used?: number;
}

export interface InteractionSummary {
  id: string;
  prompt_preview: string;
  agent_used: string;
  cognitive_state: string;
  ai_involvement: number;
  blocked: boolean;
  timestamp: string;
}

/**
 * InteractionHistory - Historial completo de interacciones de una sesión
 */
export interface InteractionHistory {
  session_id: string;
  interactions: InteractionSummary[];
  total_interactions: number;
  avg_ai_involvement: number;
  blocked_count: number;
}

// ==================== CHAT MESSAGE ====================

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  /** Cortez92: Changed from Date to string (ISO-8601) for consistency with other timestamp fields */
  timestamp: string;
  status?: MessageStatus;
  retry_count?: number;
  metadata?: {
    agent_used?: string;
    cognitive_state?: string;
    ai_involvement?: number;
    blocked?: boolean;
    block_reason?: string;
    risks_detected?: string[];
  };
}
