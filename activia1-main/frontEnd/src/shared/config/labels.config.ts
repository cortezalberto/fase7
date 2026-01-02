/**
 * Labels Configuration - UI display labels for enums
 *
 * Cortez43: Centralized label configuration for consistency
 *
 * Note: Core enum labels (RiskTypeLabels, RiskDimensionLabels, CompetencyLevelLabels)
 * are defined in src/types/domain/labels.ts and re-exported from src/types/domain/index.ts
 */

// Re-export core labels from domain types
export {
  RiskTypeLabels,
  RiskDimensionLabels,
  CompetencyLevelLabels,
} from '@/types/domain';

// Session Mode Labels
export const SessionModeLabels: Record<string, string> = {
  tutor: 'Tutor',
  evaluator: 'Evaluador',
  simulator: 'Simulador',
  practice: 'Práctica',
};

// Session Status Labels
export const SessionStatusLabels: Record<string, string> = {
  active: 'Activa',
  paused: 'Pausada',
  completed: 'Completada',
  abandoned: 'Abandonada',
};

// Risk Level Labels
export const RiskLevelLabels: Record<string, string> = {
  info: 'Información',
  low: 'Bajo',
  medium: 'Medio',
  high: 'Alto',
  critical: 'Crítico',
};

// Trace Level Labels
export const TraceLevelLabels: Record<string, string> = {
  N1: 'Nivel 1 - Básico',
  N2: 'Nivel 2 - Intermedio',
  N3: 'Nivel 3 - Avanzado',
  N4: 'Nivel 4 - Completo',
};

// Activity Difficulty Labels
export const ActivityDifficultyLabels: Record<string, string> = {
  easy: 'Fácil',
  medium: 'Medio',
  hard: 'Difícil',
  expert: 'Experto',
};

// Help Level Labels
export const HelpLevelLabels: Record<string, string> = {
  none: 'Sin ayuda',
  hint: 'Pista',
  guided: 'Guiada',
  solution: 'Solución',
};

// Cognitive Intent Labels
export const CognitiveIntentLabels: Record<string, string> = {
  understand: 'Comprender',
  apply: 'Aplicar',
  analyze: 'Analizar',
  evaluate: 'Evaluar',
  create: 'Crear',
  remember: 'Recordar',
};

// Cognitive State Labels
export const CognitiveStateLabels: Record<string, string> = {
  exploring: 'Explorando',
  confused: 'Confundido',
  progressing: 'Progresando',
  stuck: 'Atascado',
  mastering: 'Dominando',
  frustrated: 'Frustrado',
};
