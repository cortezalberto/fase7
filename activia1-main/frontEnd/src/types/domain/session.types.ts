/**
 * Session Types - Session-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 * Cortez92: Fixed redundant nullable patterns (?: with | null)
 */

import { SessionMode, SessionStatus } from './enums';

// ==================== SESSION ====================

export interface SessionCreate {
  student_id: string;
  activity_id: string;
  mode: SessionMode;
  simulator_type?: string;
}

export interface SessionUpdate {
  mode?: SessionMode;
  status?: SessionStatus;
}

export interface SessionResponse {
  id: string;
  student_id: string;
  activity_id: string;
  user_id: string | null;
  mode: string;
  status: string;
  /** Cortez92: Standardized - use only | null (field may be present but empty) */
  simulator_type: string | null;
  start_time: string;
  end_time: string | null;
  trace_count: number;
  risk_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * SessionDetailResponse - Detalle completo de una sesión
 *
 * Cortez92: Standardized nullable patterns:
 * - Use `| null` for fields always present but potentially empty
 * - Use `?:` only for truly optional fields (may not be in response)
 */
export interface SessionDetailResponse extends SessionResponse {
  traces_summary: Record<string, number>;
  risks_summary: Record<string, number>;
  ai_dependency_score: number | null;
  /** These fields may not be present in the response */
  learning_objective?: Record<string, unknown>;
  cognitive_status?: Record<string, unknown>;
  session_metrics?: Record<string, unknown>;
}
