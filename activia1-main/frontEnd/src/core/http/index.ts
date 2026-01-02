/**
 * HTTP Module - Barrel export
 *
 * Cortez43: Modular HTTP client extracted from HttpClient.ts
 */

// Main client
export { HttpClient, httpClient, ollamaClient } from './HttpClient';

// Circuit Breaker
export { CircuitBreaker } from './CircuitBreaker';
export type {
  CircuitBreakerState,
  CircuitBreakerStateType,
  CircuitBreakerConfig,
} from './CircuitBreaker';

// Metrics
export { HttpMetrics } from './HttpMetrics';
export type { HttpMetricsData } from './HttpMetrics';

// Request Queue
export { RequestQueue } from './RequestQueue';
export type { RequestQueueItem, RequestQueueConfig } from './RequestQueue';

// Utilities
export {
  isRetryableError,
  calculateBackoff,
  sleep,
  logRetry,
  generateCorrelationId,
} from './retryUtils';
export type { RetryConfig } from './retryUtils';
