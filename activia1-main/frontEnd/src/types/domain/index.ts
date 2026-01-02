/**
 * Domain Types - Re-exports from all domain-specific type files
 *
 * Cortez43: Refactored from monolithic api.types.ts (893 lines)
 *
 * This module provides modular, domain-specific type definitions while
 * maintaining full backward compatibility.
 *
 * Organization:
 * - enums.ts: All enum definitions
 * - labels.ts: UI display labels and mappings
 * - session.types.ts: Session-related interfaces
 * - interaction.types.ts: Interaction and chat interfaces
 * - trace.types.ts: Cognitive trace and traceability interfaces
 * - risk.types.ts: Risk-related interfaces
 * - evaluation.types.ts: Evaluation-related interfaces
 * - activity.types.ts: Activity-related interfaces
 * - simulator.types.ts: Simulator-related interfaces
 * - git.types.ts: Git analytics interfaces
 * - api.types.ts: Common API response wrappers
 */

// ==================== ENUMS ====================
export {
  // Session enums
  SessionMode,
  SessionStatus,
  // Cognitive enums
  CognitiveIntent,
  CognitiveState,
  CognitiveStateAlias,
  TraceLevel,
  // Risk enums
  RiskLevel,
  RiskType,
  RiskDimension,
  // Evaluation enums
  CompetencyLevel,
  // Activity enums
  ActivityDifficulty,
  ActivityStatus,
  HelpLevel,
  // Simulator enums
  SimulatorRole,
  // Cortez57: Consolidated SimulatorStatus
  type SimulatorStatus,
  // Type literals
  type AutonomyLevel,
  type DimensionLevel,
  type MessageStatus,
} from './enums';

// ==================== LABELS ====================
export {
  RiskTypeLabels,
  RiskDimensionLabels,
  CompetencyLevelLabels,
} from './labels';

// ==================== SESSION ====================
export type {
  SessionCreate,
  SessionUpdate,
  SessionResponse,
  SessionDetailResponse,
} from './session.types';

// ==================== INTERACTION ====================
export type {
  InteractionCreate,
  InteractionRequest,
  InteractionResponse,
  InteractionSummary,
  InteractionHistory,
  ChatMessage,
} from './interaction.types';

// ==================== TRACE ====================
export type {
  CognitiveTrace,
  AIDependencyPoint,
  CognitivePhase,
  CognitiveTransition,
  CognitivePathSummary,
  CognitivePath,
  TraceNode,
  Trace,
} from './trace.types';

// ==================== RISK ====================
export type {
  Risk,
  RiskDimensionScore,
  RiskAnalysis,
} from './risk.types';

// ==================== EVALUATION ====================
export type {
  EvaluationDimension,
  ConceptualError,
  ReasoningAnalysis,
  GitAnalysis,
  EvaluationReport,
  DimensionScore,
  ProcessEvaluation,
} from './evaluation.types';

// ==================== ACTIVITY ====================
export type {
  PolicyConfig,
  ActivityCreate,
  ActivityUpdate,
  ActivityResponse,
} from './activity.types';

// ==================== SIMULATOR ====================
export type {
  SimulatorInteractionRequest,
  SimulatorInteractionResponse,
} from './simulator.types';

// ==================== GIT ====================
export type {
  CommitMetrics,
  Contributor,
  CommitTrend,
  GitAnalyticsData,
} from './git.types';

// ==================== API ====================
export type {
  APIResponse,
  APIError,
  PaginationParams,
  PaginationMeta,
  PaginatedResponse,
  HealthResponse,
} from './api.types';
