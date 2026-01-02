/**
 * CircuitBreaker - Circuit breaker pattern implementation
 *
 * Cortez43: Extracted from HttpClient.ts (336 lines)
 */

// Development-only logging
const isDev = import.meta.env.DEV;
const devLog = (message: string, ...args: unknown[]) => {
  if (isDev) console.warn(message, ...args);
};
const devError = (message: string, ...args: unknown[]) => {
  if (isDev) console.error(message, ...args);
};

export type CircuitBreakerStateType = 'CLOSED' | 'OPEN' | 'HALF_OPEN';

export interface CircuitBreakerState {
  failures: number;
  lastFailure: number;
  state: CircuitBreakerStateType;
}

export interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTime: number;
}

const DEFAULT_CONFIG: CircuitBreakerConfig = {
  failureThreshold: 5,
  resetTime: 60000, // 1 minute
};

export class CircuitBreaker {
  private state: CircuitBreakerState = {
    failures: 0,
    lastFailure: 0,
    state: 'CLOSED',
  };

  private tripCount = 0;
  private readonly config: CircuitBreakerConfig;

  constructor(config: Partial<CircuitBreakerConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Check if circuit breaker allows requests
   * @throws Error if circuit is OPEN
   */
  check(): void {
    if (this.state.state === 'OPEN') {
      const error = new Error('Circuit breaker is OPEN. Service temporarily unavailable.');
      error.name = 'CircuitBreakerError';
      throw error;
    }
  }

  /**
   * Record a successful request
   */
  onSuccess(): void {
    if (this.state.state === 'HALF_OPEN') {
      this.state.state = 'CLOSED';
      this.state.failures = 0;
      devLog('[Circuit Breaker] → CLOSED (recovered)');
    }
  }

  /**
   * Record a failed request
   */
  onFailure(): void {
    this.state.failures++;
    this.state.lastFailure = Date.now();

    if (this.state.failures >= this.config.failureThreshold) {
      this.state.state = 'OPEN';
      this.tripCount++;
      devError(`[Circuit Breaker] → OPEN (${this.state.failures} failures)`);

      setTimeout(() => {
        this.state.state = 'HALF_OPEN';
        devLog('[Circuit Breaker] → HALF_OPEN (testing)');
      }, this.config.resetTime);
    }
  }

  /**
   * Get current circuit breaker state (immutable copy)
   */
  getState(): CircuitBreakerState {
    return { ...this.state };
  }

  /**
   * Get total number of times circuit has tripped
   */
  getTripCount(): number {
    return this.tripCount;
  }

  /**
   * Reset circuit breaker to initial state
   */
  reset(): void {
    this.state = {
      failures: 0,
      lastFailure: 0,
      state: 'CLOSED',
    };
  }
}
