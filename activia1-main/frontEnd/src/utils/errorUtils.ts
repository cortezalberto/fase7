/**
 * Error Utilities - Centralized error handling
 *
 * FIX Cortez71 MED-002: Centralized error message extraction
 *
 * Handles both:
 * - Interceptor-transformed errors: { success: false, error: { message, error_code } }
 * - Axios errors: AxiosError with response.data
 * - Generic errors: Error instances
 */

import axios from 'axios';

/**
 * API Error structure from interceptor
 */
interface TransformedApiError {
  success?: boolean;
  error?: {
    message?: string;
    error_code?: string;
    field?: string | null;
  };
}

/**
 * Extract error message from any error type
 *
 * @param err - Unknown error from catch block
 * @param defaultMessage - Fallback message if extraction fails
 * @returns Human-readable error message
 *
 * @example
 * try {
 *   await apiCall();
 * } catch (err) {
 *   setError(getApiErrorMessage(err, 'Error al cargar datos'));
 * }
 */
export function getApiErrorMessage(err: unknown, defaultMessage = 'Error desconocido'): string {
  // Check for interceptor-transformed error
  const apiError = err as TransformedApiError;
  if (apiError?.error?.message) {
    return apiError.error.message;
  }

  // Check for Axios error (non-transformed)
  if (axios.isAxiosError(err)) {
    return (
      err.response?.data?.error?.message ||
      err.response?.data?.detail ||
      err.message ||
      defaultMessage
    );
  }

  // Check for standard Error
  if (err instanceof Error) {
    return err.message;
  }

  return defaultMessage;
}

/**
 * Extract error code from API error
 *
 * @param err - Unknown error from catch block
 * @returns Error code string or undefined
 */
export function getApiErrorCode(err: unknown): string | undefined {
  const apiError = err as TransformedApiError;
  if (apiError?.error?.error_code) {
    return apiError.error.error_code;
  }

  if (axios.isAxiosError(err)) {
    return err.response?.data?.error?.error_code;
  }

  return undefined;
}

/**
 * Check if error is a network error
 */
export function isNetworkError(err: unknown): boolean {
  const apiError = err as TransformedApiError;
  if (apiError?.error?.error_code === 'NETWORK_ERROR') {
    return true;
  }

  if (axios.isAxiosError(err) && !err.response) {
    return true;
  }

  return false;
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(err: unknown): boolean {
  if (axios.isAxiosError(err) && err.response?.status === 401) {
    return true;
  }

  const apiError = err as TransformedApiError;
  if (apiError?.error?.error_code === 'UNAUTHORIZED' ||
      apiError?.error?.error_code === 'TOKEN_EXPIRED') {
    return true;
  }

  return false;
}

/**
 * Check if error is a validation error
 */
export function isValidationError(err: unknown): boolean {
  if (axios.isAxiosError(err) && err.response?.status === 400) {
    return true;
  }

  const apiError = err as TransformedApiError;
  if (apiError?.error?.error_code === 'VALIDATION_ERROR') {
    return true;
  }

  return false;
}

/**
 * Get validation field from error
 */
export function getValidationField(err: unknown): string | null {
  const apiError = err as TransformedApiError;
  return apiError?.error?.field || null;
}
