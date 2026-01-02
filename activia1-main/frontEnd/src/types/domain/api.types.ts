/**
 * API Types - Common API response wrappers and utilities
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

// ==================== API RESPONSE WRAPPERS ====================

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp?: string;
}

export interface APIError {
  success: false;
  error: {
    error_code: string;
    message: string;
    field: string | null;
    extra?: Record<string, unknown>;
  };
  timestamp: string;
}

// ==================== PAGINATION ====================

export interface PaginationParams {
  page: number;
  page_size: number;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMeta;
  message?: string;
}

// ==================== HEALTH ====================

/**
 * HealthResponse - Response from GET /api/v1/health
 */
export interface HealthResponse {
  status: string;
  version: string;
  database: string;
  agents: Record<string, string>;
  timestamp: string;
}
