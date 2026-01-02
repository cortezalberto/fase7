/**
 * Risk Types - Risk-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import { RiskLevel } from './enums';

// ==================== RISK ====================

/**
 * Risk - Riesgo detectado por AR-IA
 * Alineado con backend/api/routers/risks.py RiskResponse
 */
export interface Risk {
  id: string;
  session_id: string;
  student_id: string;
  activity_id: string;
  risk_type: string;
  risk_level: RiskLevel | string;
  dimension: string;
  description: string;
  impact?: string | null;
  root_cause?: string | null;
  impact_assessment?: string | null;
  evidence: string[];
  trace_ids: string[];
  recommendations: string[];
  pedagogical_intervention?: string | null;
  resolved: boolean;
  resolution_notes: string | null;
  resolved_at?: string | null;
  detected_by?: string;
  created_at: string;
  timestamp?: string;  // Legacy alias for created_at
}

// ==================== RISK ANALYSIS ====================

export interface RiskDimensionScore {
  score: number;  // 0-10 scale per dimension
  level: RiskLevel;
  indicators: string[];
}

/**
 * RiskAnalysis - Análisis de riesgo 5D completo
 *
 * Score scale:
 * - overall_score: Sum of 5 dimensions (each 0-10) = range 0-50
 * - Individual dimension scores: 0-10 scale
 */
export interface RiskAnalysis {
  session_id: string;
  overall_score: number;  // 0-50
  risk_level: RiskLevel;
  dimensions: {
    cognitive: RiskDimensionScore;
    ethical: RiskDimensionScore;
    epistemic: RiskDimensionScore;
    technical: RiskDimensionScore;
    governance: RiskDimensionScore;
  };
  top_risks: Array<{
    dimension: string;
    description: string;
    severity: RiskLevel;
    mitigation: string;
  }>;
  recommendations: string[];
}
