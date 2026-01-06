/**
 * Retry Utility - Exponential backoff retry logic for API calls
 *
 * Cortez92: Created to add resilience against transient network failures.
 * Implements exponential backoff with jitter to prevent thundering herd.
 *
 * @example
 * ```typescript
 * const result = await withRetry(
 *   () => apiClient.get('/data'),
 *   { maxRetries: 3, baseDelayMs: 1000 }
 * );
 * ```
 */

export interface RetryOptions {
  /** Maximum number of retry attempts (default: 3) */
  maxRetries?: number;
  /** Base delay in milliseconds before first retry (default: 1000) */
  baseDelayMs?: number;
  /** Maximum delay in milliseconds (default: 10000) */
  maxDelayMs?: number;
  /** Multiplier for exponential backoff (default: 2) */
  backoffMultiplier?: number;
  /** Add random jitter to prevent thundering herd (default: true) */
  useJitter?: boolean;
  /** Function to determine if error is retryable (default: network/5xx errors) */
  isRetryable?: (error: unknown) => boolean;
  /** Callback on each retry attempt */
  onRetry?: (attempt: number, error: unknown, delayMs: number) => void;
  /** AbortSignal for cancellation */
  signal?: AbortSignal;
}

const DEFAULT_OPTIONS: Required<Omit<RetryOptions, 'onRetry' | 'signal'>> = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
  backoffMultiplier: 2,
  useJitter: true,
  isRetryable: defaultIsRetryable,
};

/**
 * Default function to determine if an error is retryable.
 * Retries on network errors and 5xx server errors.
 */
function defaultIsRetryable(error: unknown): boolean {
  // Network errors (no response)
  if (error instanceof Error && error.message.includes('Network')) {
    return true;
  }

  // Axios/fetch-like error objects
  if (typeof error === 'object' && error !== null) {
    const err = error as Record<string, unknown>;

    // Axios error structure
    if ('response' in err) {
      const response = err.response as Record<string, unknown> | undefined;
      if (response && typeof response.status === 'number') {
        // Retry on 5xx server errors, 429 (rate limit), 408 (timeout)
        return response.status >= 500 || response.status === 429 || response.status === 408;
      }
      // No response = network error
      return !response;
    }

    // Check for error_code in our API error format
    if ('error' in err) {
      const apiError = err.error as Record<string, unknown> | undefined;
      if (apiError?.error_code === 'NETWORK_ERROR') {
        return true;
      }
    }
  }

  return false;
}

/**
 * Calculate delay with exponential backoff and optional jitter.
 */
function calculateDelay(
  attempt: number,
  baseDelayMs: number,
  maxDelayMs: number,
  backoffMultiplier: number,
  useJitter: boolean
): number {
  // Exponential backoff: base * multiplier^attempt
  const exponentialDelay = baseDelayMs * Math.pow(backoffMultiplier, attempt);

  // Cap at maximum delay
  const cappedDelay = Math.min(exponentialDelay, maxDelayMs);

  // Add jitter (random value between 0 and delay)
  if (useJitter) {
    const jitter = Math.random() * cappedDelay * 0.5;
    return Math.round(cappedDelay + jitter);
  }

  return Math.round(cappedDelay);
}

/**
 * Sleep for a given duration, respecting abort signal.
 */
function sleep(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }

    const timeout = setTimeout(resolve, ms);

    signal?.addEventListener('abort', () => {
      clearTimeout(timeout);
      reject(new DOMException('Aborted', 'AbortError'));
    }, { once: true });
  });
}

/**
 * Execute an async function with exponential backoff retry logic.
 *
 * @param fn - Async function to execute
 * @param options - Retry configuration options
 * @returns Promise resolving to the function result
 * @throws Last error if all retries are exhausted
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options?: RetryOptions
): Promise<T> {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  let lastError: unknown;

  for (let attempt = 0; attempt <= opts.maxRetries; attempt++) {
    // Check if aborted before each attempt
    if (opts.signal?.aborted) {
      throw new DOMException('Aborted', 'AbortError');
    }

    try {
      return await fn();
    } catch (error) {
      lastError = error;

      // Don't retry if it's not a retryable error
      if (!opts.isRetryable(error)) {
        throw error;
      }

      // Don't retry if we've exhausted attempts
      if (attempt >= opts.maxRetries) {
        throw error;
      }

      // Calculate delay for next retry
      const delayMs = calculateDelay(
        attempt,
        opts.baseDelayMs,
        opts.maxDelayMs,
        opts.backoffMultiplier,
        opts.useJitter
      );

      // Callback before retry
      opts.onRetry?.(attempt + 1, error, delayMs);

      // Wait before retrying
      await sleep(delayMs, opts.signal);
    }
  }

  // This should never be reached, but TypeScript needs it
  throw lastError;
}

/**
 * Create a retryable version of an async function.
 *
 * @example
 * ```typescript
 * const fetchWithRetry = createRetryable(
 *   (id: string) => api.get(`/items/${id}`),
 *   { maxRetries: 3 }
 * );
 * const result = await fetchWithRetry('123');
 * ```
 */
export function createRetryable<TArgs extends unknown[], TResult>(
  fn: (...args: TArgs) => Promise<TResult>,
  defaultOptions?: RetryOptions
): (...args: TArgs) => Promise<TResult> {
  return (...args: TArgs) => withRetry(() => fn(...args), defaultOptions);
}
