/**
 * useLTIContext Hook
 *
 * Cortez86: Extracted from LTIContainer.tsx to fix react-refresh warning
 *
 * Hook to access LTI context from anywhere in the app.
 */

import { use } from 'react';
import { LTIReactContext, DEFAULT_LTI_CONTEXT, type LTIContextValue } from '../contexts/LTIContext';

// Re-export types for convenience
export type { LTIContextValue } from '../contexts/LTIContext';

/**
 * Hook to access LTI context from anywhere in the app.
 *
 * @returns LTI context value
 */
export function useLTIContext(): LTIContextValue {
  const context = use(LTIReactContext);
  if (context === null) {
    // Return safe defaults when not in LTI mode
    return DEFAULT_LTI_CONTEXT;
  }
  return context;
}

export default useLTIContext;
