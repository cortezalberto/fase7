/**
 * LTI Container Component
 *
 * HU-SYS-010: Integracion con Moodle via LTI 1.3
 *
 * This component wraps the application when running in LTI mode (embedded in Moodle).
 * It provides:
 * - Detection of LTI context from URL parameters
 * - Compact layout suitable for iframe embedding
 * - Context banner showing course/activity info
 * - Session initialization from LTI launch
 *
 * Usage:
 * ```tsx
 * // In App.tsx or a route component
 * <LTIContainer>
 *   <TutorPage />
 * </LTIContainer>
 * ```
 *
 * Or use the hook directly:
 * ```tsx
 * const { isLTI, context, isLoading } = useLTIContext();
 * ```
 */

import { ReactNode, useEffect, useState, createContext, use } from 'react';
import { ltiService, LTIContext } from '../services/api/lti.service';

// =============================================================================
// Context
// =============================================================================

interface LTIContextValue {
  isLTI: boolean;
  isEmbedded: boolean;
  context: LTIContext | null;
  isLoading: boolean;
  error: string | null;
}

const LTIReactContext = createContext<LTIContextValue | null>(null);

/**
 * Hook to access LTI context from anywhere in the app.
 *
 * @returns LTI context value
 * @throws Error if used outside LTIContainer
 */
export function useLTIContext(): LTIContextValue {
  const context = use(LTIReactContext);
  if (context === null) {
    // Return safe defaults when not in LTI mode
    return {
      isLTI: false,
      isEmbedded: false,
      context: null,
      isLoading: false,
      error: null,
    };
  }
  return context;
}

// =============================================================================
// Props
// =============================================================================

interface LTIContainerProps {
  children: ReactNode;
  /** Show context banner with course info (default: true) */
  showBanner?: boolean;
  /** Compact mode - reduced padding/margins (default: auto-detect) */
  compact?: boolean;
  /** Callback when LTI context is detected */
  onLTIDetected?: (context: LTIContext) => void;
}

// =============================================================================
// Component
// =============================================================================

/**
 * LTI Container - Wrapper for LTI embedded mode.
 *
 * Automatically detects LTI context from URL parameters and provides:
 * - Compact layout for iframe embedding
 * - Context banner with course/activity info
 * - Session initialization
 */
export function LTIContainer({
  children,
  showBanner = true,
  compact,
  onLTIDetected,
}: LTIContainerProps) {
  const [isLTI, setIsLTI] = useState(false);
  const [isEmbedded, setIsEmbedded] = useState(false);
  const [context, setContext] = useState<LTIContext | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detect LTI context on mount
  useEffect(() => {
    const detectContext = () => {
      try {
        const ltiContext = ltiService.detectLTIContext();
        const embedded = ltiService.isEmbedded();

        setIsLTI(ltiContext.isLTI);
        setIsEmbedded(embedded);

        if (ltiContext.isLTI) {
          setContext(ltiContext);
          ltiService.storeLTIContext(ltiContext);

          // Notify parent
          if (onLTIDetected) {
            onLTIDetected(ltiContext);
          }

          // Clean URL params
          ltiService.cleanURL(true);
        } else {
          // Check for stored context (page refresh)
          const stored = ltiService.getStoredLTIContext();
          if (stored?.isLTI) {
            setIsLTI(true);
            setContext(stored);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to detect LTI context');
      } finally {
        setIsLoading(false);
      }
    };

    detectContext();
  }, [onLTIDetected]);

  // Determine if compact mode should be used
  const useCompact = compact ?? (isLTI || isEmbedded);

  // Build CSS classes
  const containerClasses = [
    'lti-container',
    isLTI ? 'lti-mode' : '',
    isEmbedded ? 'lti-embedded' : '',
    useCompact ? 'lti-compact' : '',
  ]
    .filter(Boolean)
    .join(' ');

  // Context value for provider
  const contextValue: LTIContextValue = {
    isLTI,
    isEmbedded,
    context,
    isLoading,
    error,
  };

  return (
    <LTIReactContext.Provider value={contextValue}>
      <div className={containerClasses}>
        {/* LTI Context Banner */}
        {isLTI && showBanner && context && (
          <LTIBanner context={context} />
        )}

        {/* Error Display */}
        {error && (
          <div className="lti-error">
            <span>Error LTI: {error}</span>
          </div>
        )}

        {/* Main Content */}
        <div className="lti-content">
          {children}
        </div>
      </div>
    </LTIReactContext.Provider>
  );
}

// =============================================================================
// Sub-components
// =============================================================================

interface LTIBannerProps {
  context: LTIContext;
}

/**
 * LTI Banner - Shows context information from Moodle.
 */
function LTIBanner({ context }: LTIBannerProps) {
  return (
    <div className="lti-banner">
      <div className="lti-banner-content">
        <span className="lti-banner-badge">
          Moodle
        </span>
        {context.contextTitle && (
          <span className="lti-banner-course">
            {context.contextTitle}
          </span>
        )}
        {context.userName && (
          <span className="lti-banner-user">
            {context.userName}
          </span>
        )}
      </div>
    </div>
  );
}

// =============================================================================
// Styles (inline for portability - can be moved to CSS)
// =============================================================================

// Add styles to document head if not already present
if (typeof document !== 'undefined') {
  const styleId = 'lti-container-styles';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
      /* LTI Container Base Styles */
      .lti-container {
        min-height: 100%;
        display: flex;
        flex-direction: column;
      }

      /* Compact mode - reduced spacing */
      .lti-compact {
        --spacing-base: 0.5rem;
      }

      .lti-compact .lti-content {
        padding: var(--spacing-base);
      }

      /* Embedded mode - no outer margins */
      .lti-embedded {
        margin: 0;
        border-radius: 0;
        box-shadow: none;
      }

      /* LTI Content Area */
      .lti-content {
        flex: 1;
        display: flex;
        flex-direction: column;
      }

      /* LTI Banner */
      .lti-banner {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        color: white;
        padding: 0.5rem 1rem;
        font-size: 0.875rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
      }

      .lti-banner-content {
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
      }

      .lti-banner-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: 600;
        font-size: 0.75rem;
        text-transform: uppercase;
      }

      .lti-banner-course {
        font-weight: 500;
      }

      .lti-banner-user {
        opacity: 0.9;
        margin-left: auto;
      }

      /* LTI Error */
      .lti-error {
        background: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 0.75rem 1rem;
        font-size: 0.875rem;
      }

      /* Hide elements in LTI mode */
      .lti-mode .hide-in-lti {
        display: none !important;
      }

      /* Show elements only in LTI mode */
      .show-in-lti {
        display: none !important;
      }

      .lti-mode .show-in-lti {
        display: block !important;
      }
    `;
    document.head.appendChild(style);
  }
}

// =============================================================================
// Exports
// =============================================================================

export default LTIContainer;
