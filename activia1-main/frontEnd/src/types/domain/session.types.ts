/**
 * Session Types - Session-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
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
  simulator_type?: string | null;
  start_time: string;
  end_time: string | null;
  trace_count: number;
  risk_count: number;
  created_at: string;
  updated_at: string;
}

/**
 * SessionDetailResponse - Detalle completo de una sesión
 */
export interface SessionDetailResponse extends SessionResponse {
  traces_summary: Record<string, number>;
  risks_summary: Record<string, number>;
  ai_dependency_score: number | null;
  learning_objective?: Record<string, unknown> | null;
  cognitive_status?: Record<string, unknown> | null;
  session_metrics?: Record<string, unknown> | null;
}
