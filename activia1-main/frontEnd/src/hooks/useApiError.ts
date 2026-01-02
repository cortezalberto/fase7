/**
 * useApiError Hook
 * FIX Cortez31: Custom hook for consistent API error handling
 *
 * Provides:
 * - Type-safe error extraction from API responses
 * - Axios error handling
 * - Network error detection
 * - User-friendly error messages
 */
import { useCallback } from 'react';

/**
 * Standard API error structure from backend
 */
export interface ApiError {
  response?: {
    data?: {
      detail?: string;
      message?: string;
      errors?: Array<{ field: string; message: string }>;
    };
    status?: number;
  };
  message?: string;
  code?: string;
  request?: unknown;
}

/**
 * Parsed error result
 */
export interface ParsedError {
  message: string;
  isNetworkError: boolean;
  isTimeout: boolean;
  isAuthError: boolean;
  isValidationError: boolean;
  status?: number;
  fieldErrors?: Array<{ field: string; message: string }>;
}

/**
 * Default error messages
 */
const DEFAULT_MESSAGES = {
  network: 'Error de conexión. Verifica tu conexión a internet.',
  timeout: 'La operación está tardando demasiado. Verifica que el servidor esté activo.',
  auth: 'Sesión expirada. Por favor, inicia sesión nuevamente.',
  validation: 'Por favor, revisa los campos del formulario.',
  server: 'Error del servidor. Intenta de nuevo más tarde.',
  unknown: 'Ha ocurrido un error inesperado.',
};

/**
 * Parse an error into a user-friendly format
 */
export function parseApiError(error: unknown): ParsedError {
  const err = error as ApiError;

  // Network error (no response)
  if (err.message === 'Network Error' || !err.response) {
    return {
      message: DEFAULT_MESSAGES.network,
      isNetworkError: true,
      isTimeout: false,
      isAuthError: false,
      isValidationError: false,
    };
  }

  // Timeout error
  if (err.code === 'ECONNABORTED') {
    return {
      message: DEFAULT_MESSAGES.timeout,
      isNetworkError: false,
      isTimeout: true,
      isAuthError: false,
      isValidationError: false,
    };
  }

  const status = err.response?.status;
  const detail = err.response?.data?.detail || err.response?.data?.message;
  const fieldErrors = err.response?.data?.errors;

  // Authentication error
  if (status === 401 || status === 403) {
    return {
      message: detail || DEFAULT_MESSAGES.auth,
      isNetworkError: false,
      isTimeout: false,
      isAuthError: true,
      isValidationError: false,
      status,
    };
  }

  // Validation error
  if (status === 422 || status === 400) {
    return {
      message: detail || DEFAULT_MESSAGES.validation,
      isNetworkError: false,
      isTimeout: false,
      isAuthError: false,
      isValidationError: true,
      status,
      fieldErrors,
    };
  }

  // Server error
  if (status && status >= 500) {
    return {
      message: detail || DEFAULT_MESSAGES.server,
      isNetworkError: false,
      isTimeout: false,
      isAuthError: false,
      isValidationError: false,
      status,
    };
  }

  // Generic error with message
  return {
    message: detail || err.message || DEFAULT_MESSAGES.unknown,
    isNetworkError: false,
    isTimeout: false,
    isAuthError: false,
    isValidationError: false,
    status,
  };
}

/**
 * Extract a simple error message from any error
 */
export function getErrorMessage(error: unknown): string {
  return parseApiError(error).message;
}

/**
 * Hook for API error handling
 *
 * @example
 * const { parseError, getErrorMessage, handleError } = useApiError();
 *
 * try {
 *   await api.fetch();
 * } catch (error) {
 *   const parsed = parseError(error);
 *   if (parsed.isAuthError) {
 *     navigate('/login');
 *   } else {
 *     showToast(parsed.message, 'error');
 *   }
 * }
 */
export function useApiError() {
  const parseError = useCallback((error: unknown): ParsedError => {
    return parseApiError(error);
  }, []);

  const getMessage = useCallback((error: unknown): string => {
    return getErrorMessage(error);
  }, []);

  /**
   * Handle error with optional callbacks
   */
  const handleError = useCallback(
    (
      error: unknown,
      options?: {
        onNetworkError?: () => void;
        onTimeout?: () => void;
        onAuthError?: () => void;
        onValidationError?: (errors?: Array<{ field: string; message: string }>) => void;
        onGenericError?: (message: string) => void;
      }
    ) => {
      const parsed = parseApiError(error);

      if (parsed.isNetworkError && options?.onNetworkError) {
        options.onNetworkError();
      } else if (parsed.isTimeout && options?.onTimeout) {
        options.onTimeout();
      } else if (parsed.isAuthError && options?.onAuthError) {
        options.onAuthError();
      } else if (parsed.isValidationError && options?.onValidationError) {
        options.onValidationError(parsed.fieldErrors);
      } else if (options?.onGenericError) {
        options.onGenericError(parsed.message);
      }

      return parsed;
    },
    []
  );

  return {
    parseError,
    getErrorMessage: getMessage,
    handleError,
  };
}

export default useApiError;
