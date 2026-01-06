/**
 * Query Builder Utility - DRY solution for URLSearchParams construction
 *
 * Cortez92: Created to eliminate 15+ instances of duplicate URLSearchParams logic
 * across API services (activities, sessions, risks, exercises, traces, etc.)
 *
 * @example
 * ```typescript
 * // Instead of manually building URLSearchParams:
 * const params = { teacher_id: 'abc', status: 'active', page: 1 };
 * const queryString = buildQueryString(params);
 * // Returns: "?teacher_id=abc&status=active&page=1"
 * ```
 */

type QueryParamValue = string | number | boolean | null | undefined;

interface QueryParams {
  [key: string]: QueryParamValue | QueryParamValue[];
}

/**
 * Builds a query string from an object of parameters.
 * Filters out null, undefined, and empty string values.
 *
 * @param params - Object containing query parameters
 * @returns Query string with leading '?' or empty string if no valid params
 */
export function buildQueryString<T extends QueryParams>(params?: T): string {
  if (!params) return '';

  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return;
    }

    if (Array.isArray(value)) {
      // Handle array values (e.g., ?ids=1&ids=2&ids=3)
      value.forEach((item) => {
        if (item !== null && item !== undefined && item !== '') {
          searchParams.append(key, String(item));
        }
      });
    } else {
      searchParams.append(key, String(value));
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * Appends query parameters to an existing URL or endpoint.
 *
 * @param endpoint - Base endpoint (e.g., '/sessions')
 * @param params - Object containing query parameters
 * @returns Endpoint with query string appended
 */
export function appendQueryParams<T extends QueryParams>(
  endpoint: string,
  params?: T
): string {
  const queryString = buildQueryString(params);
  return `${endpoint}${queryString}`;
}

/**
 * Type-safe query parameter builder with explicit field mapping.
 * Useful when backend field names differ from frontend.
 *
 * @example
 * ```typescript
 * const query = buildMappedQuery(
 *   { userId: 'abc', pageNum: 1 },
 *   { userId: 'user_id', pageNum: 'page' }
 * );
 * // Returns: "?user_id=abc&page=1"
 * ```
 */
export function buildMappedQuery<T extends Record<string, QueryParamValue>>(
  params: T,
  mapping: Partial<Record<keyof T, string>>
): string {
  const mappedParams: QueryParams = {};

  Object.entries(params).forEach(([key, value]) => {
    const mappedKey = mapping[key as keyof T] || key;
    mappedParams[mappedKey] = value;
  });

  return buildQueryString(mappedParams);
}
