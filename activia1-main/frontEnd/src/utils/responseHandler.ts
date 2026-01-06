/**
 * Response Handler Utility
 *
 * Cortez93: Centralizes response unwrapping to eliminate 9 `as unknown` assertions
 *
 * Problem: Backend inconsistently returns either:
 * - { data: T } (wrapped)
 * - { success: boolean, data: T } (API response wrapper)
 * - T (direct)
 *
 * This utility safely extracts the actual data regardless of wrapper format.
 */

/**
 * Type guard to check if response has a data property
 */
function hasDataProperty<T>(
  response: unknown
): response is { data: T } | { success: boolean; data: T } {
  return (
    response !== null &&
    typeof response === 'object' &&
    'data' in response
  );
}

/**
 * Type guard to check if response is an API response wrapper
 */
function isApiResponseWrapper<T>(
  response: unknown
): response is { success: boolean; data: T } {
  return (
    response !== null &&
    typeof response === 'object' &&
    'success' in response &&
    'data' in response
  );
}

/**
 * Unwrap API response to get the actual data
 *
 * Handles three response formats:
 * 1. { success: boolean, data: T } -> returns T
 * 2. { data: T } -> returns T
 * 3. T -> returns T
 *
 * @param response - The API response in any format
 * @returns The unwrapped data of type T
 *
 * @example
 * // All of these return the same result:
 * unwrapResponse({ success: true, data: { id: 1 } }) // { id: 1 }
 * unwrapResponse({ data: { id: 1 } })                // { id: 1 }
 * unwrapResponse({ id: 1 })                          // { id: 1 }
 */
export function unwrapResponse<T>(response: T | { data: T } | { success: boolean; data: T }): T {
  // Handle null/undefined
  if (response === null || response === undefined) {
    return response as T;
  }

  // Check for API response wrapper format first (most specific)
  if (isApiResponseWrapper<T>(response)) {
    return response.data;
  }

  // Check for simple data wrapper
  if (hasDataProperty<T>(response)) {
    return (response as { data: T }).data;
  }

  // Direct value
  return response as T;
}

/**
 * Safely unwrap response with a fallback default value
 *
 * @param response - The API response
 * @param defaultValue - Default value if unwrapping fails
 * @returns The unwrapped data or default value
 *
 * @example
 * unwrapResponseWithDefault(null, [])           // []
 * unwrapResponseWithDefault({ data: items }, []) // items
 */
export function unwrapResponseWithDefault<T>(
  response: T | { data: T } | { success: boolean; data: T } | null | undefined,
  defaultValue: T
): T {
  if (response === null || response === undefined) {
    return defaultValue;
  }

  try {
    const unwrapped = unwrapResponse(response);
    return unwrapped ?? defaultValue;
  } catch {
    return defaultValue;
  }
}

/**
 * Type-safe response unwrapper with validation
 *
 * @param response - The API response
 * @param validator - Function to validate the unwrapped data
 * @returns The validated unwrapped data or throws
 *
 * @example
 * unwrapAndValidate(response, (data) => Array.isArray(data))
 */
export function unwrapAndValidate<T>(
  response: T | { data: T } | { success: boolean; data: T },
  validator: (data: T) => boolean
): T {
  const unwrapped = unwrapResponse(response);

  if (!validator(unwrapped)) {
    throw new Error('Response validation failed');
  }

  return unwrapped;
}
