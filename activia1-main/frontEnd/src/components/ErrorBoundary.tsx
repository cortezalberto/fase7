import React, { Component, ErrorInfo, ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  // FIX Cortez48: Callback for navigation to avoid window.location
  onNavigateHome?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component to catch JavaScript errors in child component tree.
 * Prevents entire app from crashing when a component throws an error.
 *
 * Usage:
 *   <ErrorBoundary>
 *     <ComponentThatMightFail />
 *   </ErrorBoundary>
 *
 * With custom fallback:
 *   <ErrorBoundary fallback={<CustomErrorUI />}>
 *     <ComponentThatMightFail />
 *   </ErrorBoundary>
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Log error to console in development
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // In production, you might want to send this to an error tracking service
    // Example: Sentry.captureException(error, { extra: errorInfo });
  }

  handleRetry = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleGoHome = (): void => {
    // FIX Cortez48: Use callback if provided, otherwise reset state and let parent handle
    if (this.props.onNavigateHome) {
      this.props.onNavigateHome();
    } else {
      // Fallback: Reset error state - the component will re-render
      // and the user can navigate normally
      this.setState({
        hasError: false,
        error: null,
        errorInfo: null
      });
    }
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // If custom fallback is provided, use it
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="max-w-md w-full bg-[var(--bg-secondary)] border border-[var(--border-primary)] rounded-xl p-8 text-center">
            <div className="w-16 h-16 mx-auto mb-6 bg-[var(--error)]/10 rounded-full flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-[var(--error)]" />
            </div>

            <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-2">
              Algo salió mal
            </h2>

            <p className="text-[var(--text-secondary)] mb-6">
              Ha ocurrido un error inesperado. Por favor, intenta recargar la página o volver al inicio.
            </p>

            {/* Show error details in development */}
            {import.meta.env.DEV && this.state.error && (
              <details className="mb-6 text-left">
                <summary className="cursor-pointer text-sm text-[var(--text-muted)] hover:text-[var(--text-secondary)]">
                  Detalles del error (desarrollo)
                </summary>
                <div className="mt-2 p-3 bg-[var(--bg-tertiary)] rounded-lg overflow-auto max-h-40">
                  <code className="text-xs text-[var(--error)] whitespace-pre-wrap">
                    {this.state.error.toString()}
                    {this.state.errorInfo?.componentStack && (
                      <>
                        {'\n\nComponent Stack:'}
                        {this.state.errorInfo.componentStack}
                      </>
                    )}
                  </code>
                </div>
              </details>
            )}

            <div className="flex gap-3 justify-center">
              <button
                onClick={this.handleRetry}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:bg-[var(--accent-primary-hover)] transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Reintentar
              </button>

              <button
                onClick={this.handleGoHome}
                className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
              >
                <Home className="w-4 h-4" />
                Ir al inicio
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * FIX Cortez48: Wrapper component that provides React Router navigation
 * Use this instead of ErrorBoundary directly when you need navigation
 */
export function ErrorBoundaryWithNavigation({ children, ...props }: Omit<Props, 'onNavigateHome'>) {
  const navigate = useNavigate();

  const handleNavigateHome = () => {
    navigate('/dashboard');
  };

  return (
    <ErrorBoundary {...props} onNavigateHome={handleNavigateHome}>
      {children}
    </ErrorBoundary>
  );
}

export default ErrorBoundary;
