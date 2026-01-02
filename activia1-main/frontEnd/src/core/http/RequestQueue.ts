/**
 * RequestQueue - Rate-limited request queue
 *
 * Cortez43: Extracted from HttpClient.ts (336 lines)
 */

import type { AxiosRequestConfig, AxiosError } from 'axios';

export interface RequestQueueItem<T = unknown> {
  config: AxiosRequestConfig;
  resolve: (value: T) => void;
  reject: (reason: Error | AxiosError) => void;
}

export interface RequestQueueConfig {
  processDelay: number;
}

const DEFAULT_CONFIG: RequestQueueConfig = {
  processDelay: 100, // ms
};

export class RequestQueue {
  private queue: RequestQueueItem[] = [];
  private isProcessing = false;
  private readonly config: RequestQueueConfig;
  private executor: ((config: AxiosRequestConfig) => Promise<unknown>) | null = null;

  constructor(config: Partial<RequestQueueConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Set the executor function that processes queued requests
   */
  setExecutor(executor: (config: AxiosRequestConfig) => Promise<unknown>): void {
    this.executor = executor;
  }

  /**
   * Add a request to the queue
   */
  enqueue<T>(config: AxiosRequestConfig): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({
        config,
        resolve: resolve as (value: unknown) => void,
        reject,
      });

      if (!this.isProcessing) {
        this.processQueue();
      }
    });
  }

  /**
   * Process queued requests one at a time
   */
  private async processQueue(): Promise<void> {
    if (this.queue.length === 0 || !this.executor) {
      this.isProcessing = false;
      return;
    }

    this.isProcessing = true;
    const item = this.queue.shift();

    if (item) {
      try {
        const result = await this.executor(item.config);
        item.resolve(result);
      } catch (error) {
        item.reject(error as Error | AxiosError);
      }

      await this.sleep(this.config.processDelay);
      this.processQueue();
    }
  }

  /**
   * Get current queue length
   */
  get length(): number {
    return this.queue.length;
  }

  /**
   * Check if queue is currently processing
   */
  get processing(): boolean {
    return this.isProcessing;
  }

  /**
   * Clear all pending requests (rejects them)
   */
  clear(): void {
    const error = new Error('Request queue cleared');
    error.name = 'QueueClearedError';

    while (this.queue.length > 0) {
      const item = this.queue.shift();
      item?.reject(error);
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
