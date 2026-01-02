/**
 * FE-CODE-001: Custom hook for fetching sessions
 * Reduces code duplication across DashboardPage, AnalyticsPage, and other components
 * that need to fetch session data.
 */
import { useState, useEffect, useMemo, useCallback } from 'react';
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
 */
export function useFetchSessions({
  userId,
  refreshInterval = 0
}: UseFetchSessionsOptions): UseFetchSessionsResult {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch sessions function
  const fetchSessions = useCallback(async () => {
    if (!userId) {
      setIsLoading(false);
      return;
    }

    try {
      setError(null);
      const response = await sessionsService.list(userId);
      setSessions(response?.data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error fetching sessions');
      console.error('Error fetching sessions:', err);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Initial fetch and cleanup
  useEffect(() => {
    const abortController = new AbortController();

    const doFetch = async () => {
      if (!userId) {
        setIsLoading(false);
        return;
      }

      try {
        setError(null);
        const response = await sessionsService.list(userId);

        if (!abortController.signal.aborted) {
          setSessions(response?.data || []);
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          setError(err instanceof Error ? err.message : 'Error fetching sessions');
          console.error('Error fetching sessions:', err);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    doFetch();

    return () => {
      abortController.abort();
    };
  }, [userId]);

  // Auto-refresh interval
  useEffect(() => {
    if (refreshInterval > 0 && userId) {
      const intervalId = setInterval(fetchSessions, refreshInterval);
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
    refetch: fetchSessions,
    stats,
    sessionsByMode
  };
}

export default useFetchSessions;
