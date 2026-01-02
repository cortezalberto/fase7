/**
 * ErrorAlert Component
 * FIX Cortez31: Reusable error display component
 *
 * Variants:
 * - error: Red error styling (default)
 * - warning: Yellow warning styling
 * - info: Blue info styling
 */
import React from 'react';
import { AlertCircle, AlertTriangle, Info, X, RefreshCw } from 'lucide-react';

type AlertVariant = 'error' | 'warning' | 'info';

interface ErrorAlertProps {
  /** Error message to display */
  message: string;
  /** Optional title */
  title?: string;
  /** Alert variant */
  variant?: AlertVariant;
  /** Show close button */
  dismissible?: boolean;
  /** Callback when closed */
  onDismiss?: () => void;
  /** Show retry button */
  showRetry?: boolean;
  /** Callback for retry */
  onRetry?: () => void;
  /** Custom className */
  className?: string;
}

const variantStyles: Record<AlertVariant, {
  container: string;
  icon: string;
  title: string;
  text: string;
  button: string;
}> = {
  error: {
    container: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800',
    icon: 'text-red-600 dark:text-red-400',
    title: 'text-red-800 dark:text-red-300',
    text: 'text-red-700 dark:text-red-400',
    button: 'text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300',
  },
  warning: {
    container: 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800',
    icon: 'text-yellow-600 dark:text-yellow-400',
    title: 'text-yellow-800 dark:text-yellow-300',
    text: 'text-yellow-700 dark:text-yellow-400',
    button: 'text-yellow-600 hover:text-yellow-800 dark:text-yellow-400 dark:hover:text-yellow-300',
  },
  info: {
    container: 'bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800',
    icon: 'text-blue-600 dark:text-blue-400',
    title: 'text-blue-800 dark:text-blue-300',
    text: 'text-blue-700 dark:text-blue-400',
    button: 'text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300',
  },
};

const variantIcons: Record<AlertVariant, React.ElementType> = {
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

/**
 * Reusable error/warning/info alert component
 *
 * @example
 * // Simple error
 * {error && <ErrorAlert message={error} onDismiss={() => setError(null)} />}
 *
 * @example
 * // With retry button
 * <ErrorAlert
 *   message="Error al cargar datos"
 *   showRetry
 *   onRetry={loadData}
 *   onDismiss={() => setError(null)}
 * />
 *
 * @example
 * // Warning variant
 * <ErrorAlert variant="warning" message="Esta acción no se puede deshacer" />
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function ErrorAlert({
  message,
  title,
  variant = 'error',
  dismissible = true,
  onDismiss,
  showRetry = false,
  onRetry,
  className = '',
}: ErrorAlertProps) {
  const styles = variantStyles[variant];
  const Icon = variantIcons[variant];

  return (
    <div
      className={`rounded-lg border p-4 ${styles.container} ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <Icon className={`w-5 h-5 flex-shrink-0 mt-0.5 ${styles.icon}`} />

        <div className="flex-1 min-w-0">
          {title && (
            <h3 className={`font-semibold mb-1 ${styles.title}`}>{title}</h3>
          )}
          <p className={`text-sm ${styles.text}`}>{message}</p>

          {showRetry && onRetry && (
            <button
              onClick={onRetry}
              className={`mt-3 flex items-center gap-1.5 text-sm font-medium ${styles.button} transition-colors`}
            >
              <RefreshCw className="w-4 h-4" />
              Reintentar
            </button>
          )}
        </div>

        {dismissible && onDismiss && (
          <button
            onClick={onDismiss}
            className={`flex-shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors ${styles.button}`}
            aria-label="Cerrar"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

/**
 * Inline error text for forms
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function FieldError({
  message,
  className = '',
}: { message: string; className?: string }) {
  return (
    <p className={`text-sm text-red-600 dark:text-red-400 mt-1 ${className}`}>
      {message}
    </p>
  );
}

/**
 * Empty state with optional retry
 */
// FIX Cortez48: Use function component pattern instead of React.FC
interface EmptyStateProps {
  title: string;
  message?: string;
  icon?: React.ReactNode;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ title, message, icon, action }: EmptyStateProps) {
  return (
  <div className="text-center py-12">
    {icon && <div className="mb-4">{icon}</div>}
    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">{title}</h3>
    {message && <p className="text-[var(--text-secondary)] mb-4">{message}</p>}
    {action && (
      <button
        onClick={action.onClick}
        className="px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-[var(--accent-primary-hover)] transition-colors"
      >
        {action.label}
      </button>
    )}
  </div>
  );
}

export default ErrorAlert;
