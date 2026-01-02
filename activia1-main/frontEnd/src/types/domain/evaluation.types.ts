/**
 * Evaluation Types - Evaluation-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import { CompetencyLevel, AutonomyLevel, DimensionLevel } from './enums';

// ==================== EVALUATION DIMENSION ====================

/**
 * EvaluationDimension - Dimensión de evaluación
 */
export interface EvaluationDimension {
  name: string;
  description: string;
  level: CompetencyLevel | string;
  score: number;  // 0-10
  evidence: string[];
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
  // Legacy fields
  dimension?: string;  // @deprecated Use name
  feedback?: string;   // @deprecated Use recommendations
}

/**
 * ConceptualError - Error conceptual detectado
 */
export interface ConceptualError {
  error_type: string;
  description: string;
  location: string;
  severity: 'low' | 'medium' | 'high';
  recommendation: string;
}

// ==================== REASONING ANALYSIS ====================

/**
 * ReasoningAnalysis - Análisis del proceso de razonamiento
 */
export interface ReasoningAnalysis {
  // Camino cognitivo
  cognitive_path: string[];
  phases_completed: string[];
  strategy_changes: number;
  self_corrections: number;
  ai_critiques: number;
  // Análisis de coherencia
  coherence_score: number;  // 0-1
  conceptual_errors: string[];
  logical_fallacies: string[];
  // Autorregulación
  planning_quality: number;  // 0-1
  monitoring_evidence: string[];
  self_explanation_quality: number;  // 0-1
  // Legacy fields
  phases_identified?: string[];
  phase_transitions?: string[];
  reasoning_quality?: string;
  metacognitive_evidence?: string[];
  problem_solving_strategy?: string;
  completeness_score?: number;
}

// ==================== GIT ANALYSIS ====================

/**
 * GitAnalysis - Análisis de evolución del código vía Git
 */
export interface GitAnalysis {
  total_commits: number;
  commit_messages_quality: number;  // 0-1
  suspicious_jumps: string[];
  evolution_coherence: number;  // 0-1
  traces_linked: number;
  // Legacy fields
  commits_analyzed?: number;
  code_evolution_quality?: string;
  consistency_score?: number;
  patterns_detected?: string[];
  ai_generated_code_percentage?: number;
  copy_paste_detected?: boolean;
}

// ==================== EVALUATION REPORT ====================

/**
 * EvaluationReport - Reporte de evaluación completo
 */
export interface EvaluationReport {
  id: string;
  session_id: string;
  student_id: string;
  activity_id: string;
  overall_competency_level: CompetencyLevel | string;
  overall_score: number;  // 0-10 scale
  dimensions: EvaluationDimension[];
  key_strengths: string[];
  improvement_areas: string[];
  reasoning_analysis: ReasoningAnalysis | null;
  git_analysis: GitAnalysis | null;
  ai_dependency_score: number;  // 0-1
  ai_dependency_metrics: Record<string, unknown>;
  timestamp: string;
  created_at?: string;
}

// ==================== DIMENSION SCORE ====================

/**
 * DimensionScore - Puntuación de una dimensión del proceso
 */
export interface DimensionScore {
  score: number;  // 0-10
  level: DimensionLevel | string;
  evidence: string[];
  recommendations: string[];
}

// ==================== PROCESS EVALUATION ====================

/**
 * ProcessEvaluation - Evaluación completa del proceso cognitivo
 * Generated via POST /evaluations/{session_id}/generate
 */
export interface ProcessEvaluation {
  session_id: string;
  student_id: string;
  activity_id: string;
  // 5 dimensiones del proceso
  planning: DimensionScore;
  execution: DimensionScore;
  debugging: DimensionScore;
  reflection: DimensionScore;
  autonomy: DimensionScore;
  // Patrones generales
  autonomy_level: AutonomyLevel | string;
  metacognition_score: number;  // 0-10
  delegation_ratio: number;  // 0-1
  // Evidencia general
  overall_feedback: string;
  generated_at: string;
}
