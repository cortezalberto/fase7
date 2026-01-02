/**
 * Labels - UI display labels and mappings for enums
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import {
  RiskType,
  RiskDimension,
  CompetencyLevel,
} from './enums';

/**
 * Helper labels para RiskType en UI
 */
export const RiskTypeLabels: Record<RiskType, string> = {
  [RiskType.COGNITIVE_DELEGATION]: 'Delegación Cognitiva',
  [RiskType.SUPERFICIAL_REASONING]: 'Razonamiento Superficial',
  [RiskType.AI_DEPENDENCY]: 'Dependencia de IA',
  [RiskType.LACK_JUSTIFICATION]: 'Falta de Justificación',
  [RiskType.NO_SELF_REGULATION]: 'Sin Autorregulación',
  [RiskType.ACADEMIC_INTEGRITY]: 'Integridad Académica',
  [RiskType.UNDISCLOSED_AI_USE]: 'Uso No Declarado de IA',
  [RiskType.PLAGIARISM]: 'Plagio',
  [RiskType.CONCEPTUAL_ERROR]: 'Error Conceptual',
  [RiskType.LOGICAL_FALLACY]: 'Falacia Lógica',
  [RiskType.UNCRITICAL_ACCEPTANCE]: 'Aceptación Acrítica',
  [RiskType.SECURITY_VULNERABILITY]: 'Vulnerabilidad de Seguridad',
  [RiskType.POOR_CODE_QUALITY]: 'Baja Calidad de Código',
  [RiskType.ARCHITECTURAL_FLAW]: 'Fallo Arquitectónico',
  [RiskType.POLICY_VIOLATION]: 'Violación de Políticas',
  [RiskType.UNAUTHORIZED_USE]: 'Uso No Autorizado',
  [RiskType.AUTOMATION_SUSPECTED]: 'Automatización Sospechada',
};

/**
 * Helper labels para RiskDimension en UI
 */
export const RiskDimensionLabels: Record<RiskDimension, string> = {
  [RiskDimension.COGNITIVE]: 'Cognitivo',
  [RiskDimension.ETHICAL]: 'Ético',
  [RiskDimension.EPISTEMIC]: 'Epistémico',
  [RiskDimension.TECHNICAL]: 'Técnico',
  [RiskDimension.GOVERNANCE]: 'Gobernanza',
};

/**
 * Helper para mostrar CompetencyLevel en UI de forma amigable
 */
export const CompetencyLevelLabels: Record<CompetencyLevel, string> = {
  [CompetencyLevel.INICIAL]: 'Inicial',
  [CompetencyLevel.EN_DESARROLLO]: 'En Desarrollo',
  [CompetencyLevel.AUTONOMO]: 'Autónomo',
  [CompetencyLevel.EXPERTO]: 'Experto',
};
