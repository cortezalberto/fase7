/**
 * HttpMetrics - HTTP request metrics tracking
 *
 * Cortez43: Extracted from HttpClient.ts (336 lines)
 */

export interface HttpMetricsData {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  retriedRequests: number;
  averageLatency: number;
  circuitBreakerTrips: number;
}

const INITIAL_METRICS: HttpMetricsData = {
  totalRequests: 0,
  successfulRequests: 0,
  failedRequests: 0,
  retriedRequests: 0,
  averageLatency: 0,
  circuitBreakerTrips: 0,
};

export class HttpMetrics {
  private metrics: HttpMetricsData = { ...INITIAL_METRICS };

  /**
   * Record a new request
   */
  recordRequest(): void {
    this.metrics.totalRequests++;
  }

  /**
   * Record a successful request with latency
   */
  recordSuccess(latency: number): void {
    this.metrics.successfulRequests++;
    this.updateAverageLatency(latency);
  }

  /**
   * Record a failed request
   */
  recordFailure(): void {
    this.metrics.failedRequests++;
  }

  /**
   * Record a retried request
   */
  recordRetry(): void {
    this.metrics.retriedRequests++;
  }

  /**
   * Record a circuit breaker trip
   */
  recordCircuitBreakerTrip(): void {
    this.metrics.circuitBreakerTrips++;
  }

  /**
   * Update average latency using incremental average formula
   */
  private updateAverageLatency(newLatency: number): void {
    const n = this.metrics.successfulRequests;
    if (n <= 1) {
      this.metrics.averageLatency = newLatency;
    } else {
      this.metrics.averageLatency =
        (this.metrics.averageLatency * (n - 1) + newLatency) / n;
    }
  }

  /**
   * Get current metrics (immutable copy)
   */
  getMetrics(): HttpMetricsData {
    return { ...this.metrics };
  }

  /**
   * Reset all metrics to initial values
   */
  reset(): void {
    this.metrics = { ...INITIAL_METRICS };
  }
}
