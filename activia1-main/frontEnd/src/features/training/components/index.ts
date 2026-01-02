/**
 * Training Components - Barrel export
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 * Cortez55: Added V2 components for N4 traceability
 * Cortez56: Added CorreccionIADisplay for AI feedback
 */

// Core components (Cortez43)
export { LoadingState } from './LoadingState';
export { ErrorState } from './ErrorState';
export { FinalResults } from './FinalResults';
export { ProgressBar } from './ProgressBar';
export { ExerciseResultBanner } from './ExerciseResultBanner';
export { HintDisplay } from './HintDisplay';
export { ExercisePanel } from './ExercisePanel';
export { CodeEditorPanel } from './CodeEditorPanel';
export { SessionHeader } from './SessionHeader';

// V2 components for N4 traceability (Cortez55)
export { ReflexionModal } from './ReflexionModal';
export { RiskIndicator, RiskBadge } from './RiskIndicator';
export { CognitiveStateDisplay, CognitiveStateBadge } from './CognitiveStateDisplay';
export { HintV2Display } from './HintV2Display';

// Cortez56: AI Correction components
export {
  CorreccionIADisplay,
  CorreccionIABadge,
  CorreccionIAModal,
} from './CorreccionIADisplay';
