/**
 * Service Error Handler - Consistent error handling wrapper for API services
 *
 * Cortez92: Created to address inconsistent error handling across 17/22 services.
 * Provides standardized error wrapping, logging, and recovery patterns.
 *
 * @example
 * ```typescript
 * // In a service method:
 * async getUser(id: string): Promise<User> {
 *   return handleServiceError(
 *     () => this.get<User>(`/${id}`),
 *     { context: 'UserService.getUser', fallback: null }
 *   );
 * }
 * ```
 */

// Development-only logging
const isDev = import.meta.env.DEV;
const devError = (message: string, ...args: unknown[]) => {
  if (isDev) console.error(message, ...args);
};

/**
 * Standardized service error structure
 */
export interface ServiceError {
  /** Error code from backend or generated */
  code: string;
  /** Human-readable error message */
  message: string;
  /** Original error for debugging */
  originalError?: unknown;
  /** Context where error occurred */
  context?: string;
  /** Timestamp of error */
  timestamp: string;
  /** Whether this error is retryable */
  isRetryable: boolean;
}

export interface ErrorHandlerOptions<T> {
  /** Context for logging (e.g., 'UserService.getUser') */
  context?: string;
  /** Fallback value to return on error instead of throwing */
  fallback?: T;
  /** Whether to rethrow the error after handling (default: true if no fallback) */
  rethrow?: boolean;
  /** Custom error transformer */
  transformError?: (error: unknown) => ServiceError;
  /** Callback when error occurs */
  onError?: (error: ServiceError) => void;
  /** Whether to log the error (default: true in dev) */
  shouldLog?: boolean;
}

/**
 * Extract error information from various error types
 */
function extractErrorInfo(error: unknown): { code: string; message: string; isRetryable: boolean } {
  // Our API error format
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;

    // APIError structure from backend
    if ('error' in err && typeof err.error === 'object' && err.error !== null) {
      const apiError = err.error as Record<string, unknown>;
      return {
        code: String(apiError.error_code || 'API_ERROR'),
        message: String(apiError.message || 'An error occurred'),
        isRetryable: apiError.error_code === 'NETWORK_ERROR' ||
          apiError.error_code === 'SERVICE_UNAVAILABLE',
      };
    }

    // Axios error structure
    if ('response' in err) {
      const response = err.response as Record<string, unknown> | undefined;
      if (response) {
        const status = response.status as number;
        const data = response.data as Record<string, unknown> | undefined;

        return {
          code: `HTTP_${status}`,
          message: data?.message as string || getHttpStatusMessage(status),
          isRetryable: status >= 500 || status === 429 || status === 408,
        };
      }

      // No response = network error
      return {
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to server',
        isRetryable: true,
      };
    }
  }

  // Standard Error
  if (error instanceof Error) {
    return {
      code: error.name || 'ERROR',
      message: error.message,
      isRetryable: error.message.toLowerCase().includes('network'),
    };
  }

  // Unknown error type
  return {
    code: 'UNKNOWN_ERROR',
    message: String(error),
    isRetryable: false,
  };
}

/**
 * Get human-readable message for HTTP status codes
 */
function getHttpStatusMessage(status: number): string {
  const messages: Record<number, string> = {
    400: 'Invalid request',
    401: 'Authentication required',
    403: 'Access denied',
    404: 'Resource not found',
    408: 'Request timeout',
    429: 'Too many requests',
    500: 'Server error',
    502: 'Bad gateway',
    503: 'Service unavailable',
    504: 'Gateway timeout',
  };
  return messages[status] || `HTTP error ${status}`;
}

/**
 * Create a standardized ServiceError from any error type
 */
export function createServiceError(
  error: unknown,
  context?: string
): ServiceError {
  const { code, message, isRetryable } = extractErrorInfo(error);

  return {
    code,
    message,
    originalError: error,
    context,
    timestamp: new Date().toISOString(),
    isRetryable,
  };
}

/**
 * Handle service errors with consistent logging and optional fallback.
 *
 * @param fn - Async function to execute
 * @param options - Error handling options
 * @returns Promise resolving to result or fallback
 */
export async function handleServiceError<T>(
  fn: () => Promise<T>,
  options: ErrorHandlerOptions<T> = {}
): Promise<T> {
  const {
    context,
    fallback,
    rethrow = fallback === undefined,
    transformError,
    onError,
    shouldLog = isDev,
  } = options;

  try {
    return await fn();
  } catch (error) {
    const serviceError = transformError
      ? transformError(error)
      : createServiceError(error, context);

    // Log in development
    if (shouldLog) {
      devError(
        `[ServiceError] ${context || 'Unknown context'}:`,
        serviceError.message,
        { code: serviceError.code, isRetryable: serviceError.isRetryable }
      );
    }

    // Custom error callback
    onError?.(serviceError);

    // Return fallback or rethrow
    if (rethrow) {
      throw serviceError;
    }

    return fallback as T;
  }
}

/**
 * Wrap a service method with consistent error handling.
 *
 * @example
 * ```typescript
 * class MyService {
 *   getUser = withErrorHandler(
 *     (id: string) => this.get<User>(`/${id}`),
 *     { context: 'MyService.getUser' }
 *   );
 * }
 * ```
 */
export function withErrorHandler<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>,
  options: ErrorHandlerOptions<TResult> = {}
): (...args: TArgs) => Promise<TResult> {
  return (...args: TArgs) => handleServiceError(() => fn(...args), options);
}

/**
 * Type guard to check if an error is a ServiceError
 */
export function isServiceError(error: unknown): error is ServiceError {
  return (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    'message' in error &&
    'timestamp' in error &&
    'isRetryable' in error
  );
}

/**
 * Check if an error indicates the request was aborted
 */
export function isAbortError(error: unknown): boolean {
  if (error instanceof DOMException && error.name === 'AbortError') {
    return true;
  }
  if (error instanceof Error && error.name === 'AbortError') {
    return true;
  }
  return false;
}
