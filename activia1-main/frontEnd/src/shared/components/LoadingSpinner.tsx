/**
 * LoadingSpinner Component
 * FIX Cortez31: Reusable loading spinner component
 *
 * Variants:
 * - default: Standard spinner
 * - small: Compact spinner for buttons
 * - large: Full-screen centered spinner
 * - overlay: Spinner with backdrop overlay
 */
import React from 'react';
import { Loader2 } from 'lucide-react';

type SpinnerSize = 'small' | 'default' | 'large';
type SpinnerVariant = 'default' | 'overlay' | 'fullscreen';

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: SpinnerSize;
  /** Display variant */
  variant?: SpinnerVariant;
  /** Optional message to display */
  message?: string;
  /** Custom className */
  className?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  small: 'w-4 h-4',
  default: 'w-8 h-8',
  large: 'w-12 h-12',
};

/**
 * Reusable loading spinner
 *
 * @example
 * // In button
 * <button disabled={loading}>
 *   {loading ? <LoadingSpinner size="small" /> : 'Submit'}
 * </button>
 *
 * @example
 * // Full screen
 * {loading && <LoadingSpinner variant="fullscreen" message="Cargando..." />}
 *
 * @example
 * // Overlay on container
 * <div className="relative">
 *   <Content />
 *   {loading && <LoadingSpinner variant="overlay" />}
 * </div>
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function LoadingSpinner({
  size = 'default',
  variant = 'default',
  message,
  className = '',
}: LoadingSpinnerProps) {
  const spinnerIcon = (
    <Loader2
      className={`${sizeClasses[size]} animate-spin text-[var(--accent-primary)]`}
    />
  );

  if (variant === 'fullscreen') {
    return (
      <div className={`fixed inset-0 flex flex-col items-center justify-center bg-[var(--bg-primary)] z-50 ${className}`}>
        {spinnerIcon}
        {message && (
          <p className="mt-4 text-[var(--text-secondary)] text-sm">{message}</p>
        )}
      </div>
    );
  }

  if (variant === 'overlay') {
    return (
      <div className={`absolute inset-0 flex flex-col items-center justify-center bg-[var(--bg-primary)]/80 backdrop-blur-sm z-10 ${className}`}>
        {spinnerIcon}
        {message && (
          <p className="mt-4 text-[var(--text-secondary)] text-sm">{message}</p>
        )}
      </div>
    );
  }

  // Default inline spinner
  if (message) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {spinnerIcon}
        <span className="text-[var(--text-secondary)] text-sm">{message}</span>
      </div>
    );
  }

  return <span className={className}>{spinnerIcon}</span>;
};

/**
 * Simple inline spinner for buttons
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function ButtonSpinner({ className }: { className?: string }) {
  return (
    <Loader2 className={`w-4 h-4 animate-spin ${className || ''}`} />
  );
}

/**
 * Page loading state
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function PageLoader({ message = 'Cargando...' }: { message?: string }) {
  return (
  <div className="flex items-center justify-center h-64">
    <div className="text-center">
      <Loader2 className="w-8 h-8 text-[var(--accent-primary)] animate-spin mx-auto mb-4" />
      <p className="text-[var(--text-secondary)]">{message}</p>
    </div>
  </div>
  );
}

export default LoadingSpinner;
