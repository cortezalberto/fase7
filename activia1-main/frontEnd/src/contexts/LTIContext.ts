/**
 * LTI Context
 *
 * Cortez86: Extracted from LTIContainer.tsx to fix react-refresh warning
 *
 * Provides LTI context for the application when running in Moodle LTI mode.
 */

import { createContext } from 'react';
import type { LTIContext as LTIContextData } from '../services/api/lti.service';

// =============================================================================
// Types
// =============================================================================

export interface LTIContextValue {
  isLTI: boolean;
  isEmbedded: boolean;
  context: LTIContextData | null;
  isLoading: boolean;
  error: string | null;
}

// =============================================================================
// Context
// =============================================================================

export const LTIReactContext = createContext<LTIContextValue | null>(null);

// =============================================================================
// Default value for when not in LTI mode
// =============================================================================

export const DEFAULT_LTI_CONTEXT: LTIContextValue = {
  isLTI: false,
  isEmbedded: false,
  context: null,
  isLoading: false,
  error: null,
};
