/**
 * useAsyncOperation Hook
 * FIX Cortez31: Custom hook for async operations with automatic isMounted tracking
 *
 * Provides:
 * - Automatic isMounted check to prevent state updates after unmount
 * - Loading state management
 * - Error state management
 * - Execute function with type-safe return
 */
import { useState, useRef, useEffect, useCallback } from 'react';

interface AsyncOperationState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface AsyncOperationResult<T> extends AsyncOperationState<T> {
  execute: (asyncFn: () => Promise<T>) => Promise<T | null>;
  reset: () => void;
  setData: (data: T | null) => void;
}

/**
 * Hook for handling async operations safely
 *
 * @example
 * const { data, loading, error, execute } = useAsyncOperation<User[]>();
 *
 * const loadUsers = async () => {
 *   return await userService.list();
 * };
 *
 * useEffect(() => {
 *   execute(loadUsers);
 * }, [execute]);
 */
export function useAsyncOperation<T>(
  initialData: T | null = null
): AsyncOperationResult<T> {
  const [state, setState] = useState<AsyncOperationState<T>>({
    data: initialData,
    loading: false,
    error: null,
  });

  // Track if component is mounted
  const isMountedRef = useRef<boolean>(true);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  /**
   * Execute an async operation safely
   * Returns null if component unmounts during execution
   */
  const execute = useCallback(
    async (asyncFn: () => Promise<T>): Promise<T | null> => {
      if (!isMountedRef.current) return null;

      setState(prev => ({ ...prev, loading: true, error: null }));

      try {
        const result = await asyncFn();

        if (isMountedRef.current) {
          setState({ data: result, loading: false, error: null });
          return result;
        }
        return null;
      } catch (err) {
        if (isMountedRef.current) {
          const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
          setState(prev => ({ ...prev, loading: false, error: errorMessage }));
        }
        return null;
      }
    },
    []
  );

  /**
   * Reset state to initial values
   * Cortez93: Removed initialData from dependencies to prevent unnecessary callback recreation
   * The initialData is captured at hook call time which is the expected behavior
   */
  const reset = useCallback(() => {
    if (isMountedRef.current) {
      setState({ data: initialData, loading: false, error: null });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Manually set data (useful for optimistic updates)
   */
  const setData = useCallback((data: T | null) => {
    if (isMountedRef.current) {
      setState(prev => ({ ...prev, data }));
    }
  }, []);

  return {
    ...state,
    execute,
    reset,
    setData,
  };
}

/**
 * Simpler hook that just provides isMounted ref for manual use
 *
 * @example
 * const isMounted = useIsMounted();
 *
 * const handleClick = async () => {
 *   const data = await api.fetch();
 *   if (isMounted()) {
 *     setState(data);
 *   }
 * };
 */
export function useIsMounted(): () => boolean {
  const isMountedRef = useRef<boolean>(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return useCallback(() => isMountedRef.current, []);
}

export default useAsyncOperation;
