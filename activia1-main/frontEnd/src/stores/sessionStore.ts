/**
 * Session Store - Zustand store for current session state
 * FIX Cortez31: Migrated from AppContext to Zustand
 * FIX Cortez32: Import ActiveSession from types to avoid duplication
 *
 * Manages:
 * - Current active learning session
 * - Session status for UI display
 *
 * Note: This is for UI state only. Session persistence/auth is handled by AuthContext.
 */
import { create } from 'zustand';
import type { ActiveSession } from '@/types';

// Re-export for convenience
export type { ActiveSession };

interface SessionState {
  currentSession: ActiveSession | null;
}

interface SessionActions {
  setSession: (session: ActiveSession | null) => void;
  clearSession: () => void;
  updateSessionStatus: (isActive: boolean) => void;
}

type SessionStore = SessionState & SessionActions;

const initialState: SessionState = {
  currentSession: null,
};

/**
 * Session Store for managing current learning session
 *
 * @example
 * // In a component:
 * const session = useSessionStore(state => state.currentSession);
 * const setSession = useSessionStore(state => state.setSession);
 *
 * // Start a new session
 * setSession({ id: 'abc123', mode: 'TUTOR', student_id: 'user1', is_active: true });
 *
 * // Clear session on logout
 * const clearSession = useSessionStore(state => state.clearSession);
 * clearSession();
 */
export const useSessionStore = create<SessionStore>()((set) => ({
  // State
  ...initialState,

  // Actions
  setSession: (session: ActiveSession | null) => {
    set({ currentSession: session });
  },

  clearSession: () => {
    set({ currentSession: null });
  },

  updateSessionStatus: (isActive: boolean) => {
    set((state) => {
      if (!state.currentSession) return state;
      return {
        currentSession: {
          ...state.currentSession,
          is_active: isActive,
        },
      };
    });
  },
}));

// Selector hooks for better performance
export const useCurrentSession = () => useSessionStore((state) => state.currentSession);
export const useSetSession = () => useSessionStore((state) => state.setSession);
export const useClearSession = () => useSessionStore((state) => state.clearSession);
export const useIsSessionActive = () =>
  useSessionStore((state) => state.currentSession?.is_active ?? false);
