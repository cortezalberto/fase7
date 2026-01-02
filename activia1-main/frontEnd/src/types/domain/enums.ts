/**
 * Enums - All enum definitions for the AI-Native ecosystem
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

// ==================== SESSION ENUMS ====================

/**
 * SessionMode - Modos operativos del motor cognitivo
 * Alineado con backend/core/cognitive_engine.py AgentMode
 */
export enum SessionMode {
  TUTOR = 'TUTOR',
  EVALUATOR = 'EVALUATOR',
  SIMULATOR = 'SIMULATOR',
  RISK_ANALYST = 'RISK_ANALYST',
  GOVERNANCE = 'GOVERNANCE',
  PRACTICE = 'PRACTICE',
}

export enum SessionStatus {
  ACTIVE = 'active',
  COMPLETED = 'completed',
  PAUSED = 'paused',
  ABORTED = 'aborted',
  ABANDONED = 'abandoned',
}

// ==================== COGNITIVE ENUMS ====================

export enum CognitiveIntent {
  UNDERSTANDING = 'UNDERSTANDING',
  EXPLORATION = 'EXPLORATION',
  PLANNING = 'PLANNING',
  IMPLEMENTATION = 'IMPLEMENTATION',
  DEBUGGING = 'DEBUGGING',
  VALIDATION = 'VALIDATION',
  REFLECTION = 'REFLECTION',
  UNKNOWN = 'UNKNOWN',
}

export enum CognitiveState {
  EXPLORACION = 'exploracion',
  PLANIFICACION = 'planificacion',
  IMPLEMENTACION = 'implementacion',
  DEPURACION = 'depuracion',
  VALIDACION = 'validacion',
  REFLEXION = 'reflexion',
}

// English aliases for backwards compatibility
export const CognitiveStateAlias = {
  EXPLORATION: CognitiveState.EXPLORACION,
  PLANNING: CognitiveState.PLANIFICACION,
  IMPLEMENTATION: CognitiveState.IMPLEMENTACION,
  DEBUGGING: CognitiveState.DEPURACION,
  VALIDATION: CognitiveState.VALIDACION,
  REFLECTION: CognitiveState.REFLEXION,
} as const;

export enum TraceLevel {
  N1_SUPERFICIAL = 'n1_superficial',
  N2_TECNICO = 'n2_tecnico',
  N3_INTERACCIONAL = 'n3_interaccional',
  N4_COGNITIVO = 'n4_cognitivo',
}

// ==================== RISK ENUMS ====================

export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
  INFO = 'info',
}

/**
 * RiskType - Tipos de riesgo según AR-IA
 * Alineado con backend/models/risk.py RiskType
 */
export enum RiskType {
  // Riesgos Cognitivos (RC)
  COGNITIVE_DELEGATION = 'cognitive_delegation',
  SUPERFICIAL_REASONING = 'superficial_reasoning',
  AI_DEPENDENCY = 'ai_dependency',
  LACK_JUSTIFICATION = 'lack_justification',
  NO_SELF_REGULATION = 'no_self_regulation',
  // Riesgos Éticos (RE)
  ACADEMIC_INTEGRITY = 'academic_integrity',
  UNDISCLOSED_AI_USE = 'undisclosed_ai_use',
  PLAGIARISM = 'plagiarism',
  // Riesgos Epistémicos (REp)
  CONCEPTUAL_ERROR = 'conceptual_error',
  LOGICAL_FALLACY = 'logical_fallacy',
  UNCRITICAL_ACCEPTANCE = 'uncritical_acceptance',
  // Riesgos Técnicos (RT)
  SECURITY_VULNERABILITY = 'security_vulnerability',
  POOR_CODE_QUALITY = 'poor_code_quality',
  ARCHITECTURAL_FLAW = 'architectural_flaw',
  // Riesgos de Gobernanza (RG)
  POLICY_VIOLATION = 'policy_violation',
  UNAUTHORIZED_USE = 'unauthorized_use',
  AUTOMATION_SUSPECTED = 'automation_suspected',
}

/**
 * RiskDimension - Dimensiones de riesgo según ISO/IEC 23894
 * Alineado con backend/models/risk.py RiskDimension
 */
export enum RiskDimension {
  COGNITIVE = 'cognitive',
  ETHICAL = 'ethical',
  EPISTEMIC = 'epistemic',
  TECHNICAL = 'technical',
  GOVERNANCE = 'governance',
}

// ==================== EVALUATION ENUMS ====================

/**
 * CompetencyLevel - Niveles de competencia del estudiante
 * Alineado con backend/models/evaluation.py CompetencyLevel
 */
export enum CompetencyLevel {
  INICIAL = 'inicial',
  EN_DESARROLLO = 'en_desarrollo',
  AUTONOMO = 'autonomo',
  EXPERTO = 'experto',
}

// ==================== ACTIVITY ENUMS ====================

export enum ActivityDifficulty {
  INICIAL = 'INICIAL',
  INTERMEDIO = 'INTERMEDIO',
  AVANZADO = 'AVANZADO',
}

export enum ActivityStatus {
  DRAFT = 'draft',
  ACTIVE = 'active',
  ARCHIVED = 'archived',
}

export enum HelpLevel {
  MINIMO = 'minimo',
  BAJO = 'bajo',
  MEDIO = 'medio',
  ALTO = 'alto',
}

// ==================== SIMULATOR ENUMS ====================

/**
 * SimulatorRole - Roles de simulador profesional
 * Alineado con backend SimulatorType enum
 */
export enum SimulatorRole {
  // V1 - Original simulators
  PRODUCT_OWNER = 'product_owner',
  SCRUM_MASTER = 'scrum_master',
  TECH_INTERVIEWER = 'tech_interviewer',
  INCIDENT_RESPONDER = 'incident_responder',
  CLIENT = 'client',
  DEVSECOPS = 'devsecops',
  // V2 - Enhanced simulators (Sprint 6)
  SENIOR_DEV = 'senior_dev',
  QA_ENGINEER = 'qa_engineer',
  SECURITY_AUDITOR = 'security_auditor',
  TECH_LEAD = 'tech_lead',
  DEMANDING_CLIENT = 'demanding_client',
}

/**
 * SimulatorStatus - Estado del simulador
 * Cortez57: Consolidado desde simulators.service.ts
 */
export type SimulatorStatus = 'active' | 'development' | 'deprecated';

// ==================== TYPE LITERALS ====================

export type AutonomyLevel = 'low' | 'medium' | 'high';
export type DimensionLevel = 'novice' | 'competent' | 'proficient' | 'expert';
export type MessageStatus = 'pending' | 'sent' | 'retrying' | 'failed';
