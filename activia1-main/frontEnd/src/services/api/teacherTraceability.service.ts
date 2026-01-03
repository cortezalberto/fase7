/**
 * Teacher Traceability Service - N4 Cognitive Traceability for Teachers
 *
 * Cortez63: New endpoints for teacher access to student traceability
 *
 * Backend endpoints:
 * - GET /api/v1/teacher/students/{student_id}/traceability
 * - GET /api/v1/teacher/students/{student_id}/cognitive-path
 * - GET /api/v1/teacher/traceability/summary
 */

import apiClient from './client';

// =====================================================================
// TYPES
// =====================================================================

/** Trace level (N1-N4) */
export type TraceLevel = 'N1' | 'N2' | 'N3' | 'N4';

/** Cognitive state */
export type CognitiveState =
  | 'INICIO'
  | 'EXPLORACION'
  | 'IMPLEMENTACION'
  | 'DEPURACION'
  | 'CAMBIO_ESTRATEGIA'
  | 'VALIDACION'
  | 'ESTANCAMIENTO'
  | 'REFLEXION';

/** Individual trace data */
export interface TraceData {
  id: string;
  session_id: string;
  activity_id: string | null;
  trace_level: TraceLevel | null;
  interaction_type: string | null;
  cognitive_state: CognitiveState | null;
  cognitive_intent: string | null;
  decision_justification: string | null;
  strategy_type: string | null;
  ai_involvement: number | null;
  content: string | null;
  agent_id: string | null;
  created_at: string | null;
}

/** Pagination info */
export interface PaginationInfo {
  offset: number;
  limit: number;
  has_more: boolean;
}

/** Traceability summary for a student */
export interface TraceabilitySummary {
  cognitive_states_distribution: Record<string, number>;
  trace_levels_distribution: Record<string, number>;
  interaction_types_distribution: Record<string, number>;
  average_ai_involvement: number;
  total_n4_traces: number;
}

/** Student traceability response */
export interface StudentTraceabilityResponse {
  student_id: string;
  activity_id: string | null;
  total_traces: number;
  returned_traces: number;
  pagination: PaginationInfo;
  summary: TraceabilitySummary;
  traces: TraceData[];
}

/** Cognitive path state */
export interface CognitivePathState {
  state: CognitiveState;
  timestamp: string | null;
  ai_involvement: number | null;
  trace_level: TraceLevel | null;
  session_id: string;
}

/** Cognitive transition */
export interface CognitiveTransition {
  from: CognitiveState;
  to: CognitiveState;
  timestamp: string | null;
}

/** Student cognitive path response */
export interface StudentCognitivePathResponse {
  student_id: string;
  session_id: string | null;
  total_states: number;
  unique_states: CognitiveState[];
  cognitive_path: CognitivePathState[];
  transitions: CognitiveTransition[];
  time_in_states: Record<string, number>;
  insights: string[];
}

/** AI dependency distribution */
export interface AIDependencyDistribution {
  high: number;
  medium: number;
  low: number;
}

/** Traceability alert */
export interface TraceabilityAlert {
  type: 'high_ai_dependency' | 'high_stagnation';
  severity: 'warning' | 'critical';
  message: string;
  students?: string[];
}

/** Global traceability summary response */
export interface TraceabilitySummaryResponse {
  activity_id: string | null;
  total_students: number;
  total_traces: number;
  cognitive_states_global: Record<string, number>;
  ai_dependency_distribution: AIDependencyDistribution;
  students_by_ai_dependency: {
    high: string[];
    medium: string[];
    low: string[];
  };
  alerts: TraceabilityAlert[];
}

/** Query params for student traceability */
export interface StudentTraceabilityParams {
  activity_id?: string;
  limit?: number;
  offset?: number;
}

/** Query params for cognitive path */
export interface CognitivePathParams {
  session_id?: string;
}

/** Query params for traceability summary */
export interface TraceabilitySummaryParams {
  activity_id?: string;
}

// =====================================================================
// SERVICE
// =====================================================================

/**
 * Teacher Traceability Service
 *
 * Provides access to N4 cognitive traceability data for teachers.
 */
export const teacherTraceabilityService = {
  /**
   * Get traceability for a specific student
   *
   * @param studentId - Student ID
   * @param params - Optional query parameters
   * @returns Student traceability data with traces and summary
   */
  async getStudentTraceability(
    studentId: string,
    params?: StudentTraceabilityParams
  ): Promise<StudentTraceabilityResponse> {
    const queryParams = new URLSearchParams();

    if (params?.activity_id) {
      queryParams.append('activity_id', params.activity_id);
    }
    if (params?.limit !== undefined) {
      queryParams.append('limit', params.limit.toString());
    }
    if (params?.offset !== undefined) {
      queryParams.append('offset', params.offset.toString());
    }

    const queryString = queryParams.toString();
    const url = `/teacher/students/${studentId}/traceability${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<{ data: StudentTraceabilityResponse }>(url);
    return 'data' in response.data ? response.data.data : (response.data as unknown as StudentTraceabilityResponse);
  },

  /**
   * Get cognitive path for a specific student
   *
   * @param studentId - Student ID
   * @param params - Optional query parameters
   * @returns Student cognitive path with transitions and insights
   */
  async getStudentCognitivePath(
    studentId: string,
    params?: CognitivePathParams
  ): Promise<StudentCognitivePathResponse> {
    const queryParams = new URLSearchParams();

    if (params?.session_id) {
      queryParams.append('session_id', params.session_id);
    }

    const queryString = queryParams.toString();
    const url = `/teacher/students/${studentId}/cognitive-path${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<{ data: StudentCognitivePathResponse }>(url);
    return 'data' in response.data ? response.data.data : (response.data as unknown as StudentCognitivePathResponse);
  },

  /**
   * Get global traceability summary for all students
   *
   * @param params - Optional query parameters
   * @returns Aggregated traceability metrics and alerts
   */
  async getTraceabilitySummary(
    params?: TraceabilitySummaryParams
  ): Promise<TraceabilitySummaryResponse> {
    const queryParams = new URLSearchParams();

    if (params?.activity_id) {
      queryParams.append('activity_id', params.activity_id);
    }

    const queryString = queryParams.toString();
    const url = `/teacher/traceability/summary${queryString ? `?${queryString}` : ''}`;

    const response = await apiClient.get<{ data: TraceabilitySummaryResponse }>(url);
    return 'data' in response.data ? response.data.data : (response.data as unknown as TraceabilitySummaryResponse);
  },
};

export default teacherTraceabilityService;
