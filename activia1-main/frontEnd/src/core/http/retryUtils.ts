/**
 * Retry Utilities - Retry logic and backoff calculation
 *
 * Cortez43: Extracted from HttpClient.ts (336 lines)
 */

import type { AxiosError } from 'axios';

// Development-only logging
const isDev = import.meta.env.DEV;
const devLog = (message: string, ...args: unknown[]) => {
  if (isDev) console.warn(message, ...args);
};

export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
}

const DEFAULT_CONFIG: RetryConfig = {
  maxAttempts: 3,
  baseDelay: 1000,
  maxDelay: 10000,
};

/**
 * Check if an error is retryable
 */
export function isRetryableError(error: AxiosError): boolean {
  // Network errors, timeouts
  if (!error.response) {
    return true;
  }

  const status = error.response.status;
  // Retry on 5xx and specific 4xx
  return status >= 500 || status === 408 || status === 429;
}

/**
 * Calculate exponential backoff delay with jitter
 */
export function calculateBackoff(
  retryCount: number,
  config: Partial<RetryConfig> = {}
): number {
  const { baseDelay, maxDelay } = { ...DEFAULT_CONFIG, ...config };

  // Exponential backoff with jitter
  const exponentialDelay = baseDelay * Math.pow(2, retryCount - 1);
  const jitter = Math.random() * 200;
  return Math.min(exponentialDelay + jitter, maxDelay);
}

/**
 * Sleep utility
 */
export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Log retry attempt
 */
export function logRetry(attempt: number, maxAttempts: number, delay: number): void {
  devLog(`[HTTP ↻] Retry ${attempt}/${maxAttempts} after ${delay}ms`);
}

/**
 * Generate correlation ID for request tracing
 */
export function generateCorrelationId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
