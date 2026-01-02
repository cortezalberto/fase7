/**
 * Simulator Types - Simulator-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import { SimulatorRole } from './enums';

// ==================== SIMULATOR INTERACTION ====================

export interface SimulatorInteractionRequest {
  role: SimulatorRole;
  message: string;
  context?: Record<string, unknown>;
}

export interface SimulatorInteractionResponse {
  role: SimulatorRole;
  response: string;
  evaluation: {
    score: number;
    feedback: string;
    suggestions: string[];
  };
  metadata: {
    model: string;
    tokens_used: number;
    processing_time_ms: number;
  };
}
