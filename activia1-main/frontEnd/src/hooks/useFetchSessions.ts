/**
 * FE-CODE-001: Custom hook for fetching sessions
 * Reduces code duplication across DashboardPage, AnalyticsPage, and other components
 * that need to fetch session data.
 *
 * Cortez92: Fixed duplicate fetch logic, consolidated into single function with AbortController
 */
import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { sessionsService } from '../services/api';
import { Session } from '../types';

interface UseFetchSessionsOptions {
  /** User ID to fetch sessions for */
  userId: string | undefined;
  /** Enable auto-refresh at interval (ms). Set to 0 to disable */
  refreshInterval?: number;
}

interface UseFetchSessionsResult {
  /** Array of sessions */
  sessions: Session[];
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Refetch sessions manually */
  refetch: () => Promise<void>;
  /** Computed statistics */
  stats: {
    totalSessions: number;
    activeSessions: number;
    completedSessions: number;
    totalInteractions: number;
    completionRate: number;
    avgInteractionsPerSession: number;
  };
  /** Sessions grouped by mode */
  sessionsByMode: {
    TUTOR: number;
    SIMULATOR: number;
    PRACTICE: number;
  };
}

/**
 * Custom hook to fetch and manage session data
 * Provides memoized statistics and auto-refresh capability
 *
 * Cortez92: Consolidated fetch logic to eliminate duplication
 */
export function useFetchSessions({
  userId,
  refreshInterval = 0
}: UseFetchSessionsOptions): UseFetchSessionsResult {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cortez92: Use ref to track if component is mounted
  const isMountedRef = useRef(true);
  // Cortez92: Track current abort controller for cleanup
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cortez92: Consolidated fetch function with abort support
  const fetchSessions = useCallback(async (isInitialLoad = false) => {
    if (!userId) {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
      return;
    }

    // Cancel any in-flight request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      if (isInitialLoad) {
        setIsLoading(true);
      }
      setError(null);

      const response = await sessionsService.list(userId);

      // Check if request was aborted or component unmounted
      if (controller.signal.aborted || !isMountedRef.current) {
        return;
      }

      setSessions(response?.data || []);
    } catch (err) {
      // Ignore abort errors
      if (err instanceof DOMException && err.name === 'AbortError') {
        return;
      }

      if (!controller.signal.aborted && isMountedRef.current) {
        const errorMessage = err instanceof Error ? err.message : 'Error fetching sessions';
        setError(errorMessage);
        if (import.meta.env.DEV) {
          console.error('Error fetching sessions:', err);
        }
      }
    } finally {
      if (!controller.signal.aborted && isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [userId]);

  // Public refetch function (marks as non-initial load)
  const refetch = useCallback(async () => {
    await fetchSessions(false);
  }, [fetchSessions]);

  // Initial fetch and cleanup
  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch
    fetchSessions(true);

    return () => {
      isMountedRef.current = false;
      // Abort any in-flight request on unmount
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchSessions]);

  // Auto-refresh interval
  useEffect(() => {
    if (refreshInterval > 0 && userId) {
      const intervalId = setInterval(() => {
        fetchSessions(false);
      }, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval, userId, fetchSessions]);

  // Memoized statistics
  const stats = useMemo(() => {
    const totalSessions = sessions.length;
    const activeSessions = sessions.filter(s => s.status === 'active').length;
    const completedSessions = sessions.filter(s => s.status === 'completed').length;
    const totalInteractions = sessions.reduce((acc, s) => acc + (s.trace_count || 0), 0);
    const completionRate = totalSessions > 0
      ? Math.round((completedSessions / totalSessions) * 100)
      : 0;
    const avgInteractionsPerSession = totalSessions > 0
      ? Math.round(totalInteractions / totalSessions)
      : 0;

    return {
      totalSessions,
      activeSessions,
      completedSessions,
      totalInteractions,
      completionRate,
      avgInteractionsPerSession
    };
  }, [sessions]);

  // Memoized sessions by mode
  const sessionsByMode = useMemo(() => ({
    TUTOR: sessions.filter(s => s.mode === 'TUTOR').length,
    SIMULATOR: sessions.filter(s => s.mode === 'SIMULATOR').length,
    PRACTICE: sessions.filter(s => s.mode === 'PRACTICE').length
  }), [sessions]);

  return {
    sessions,
    isLoading,
    error,
    refetch,
    stats,
    sessionsByMode
  };
}

export default useFetchSessions;
