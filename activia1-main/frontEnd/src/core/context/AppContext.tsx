/**
 * Context global de la aplicación con estado optimizado - React 19
 *
 * FIX Cortez31: Removed duplicate user state - AuthContext handles user authentication
 * FIX Cortez32: Import ActiveSession from types to avoid duplication
 * AppContext now focuses on UI state only:
 * - Theme (light/dark)
 * - Sidebar collapsed state
 * - Current session (for UI display only)
 *
 * Migrated to React 19 with:
 * - New `use()` hook for context consumption
 * - Improved typing with Dispatch from react
 * - Function component pattern without React.FC
 */
import { createContext, useReducer, useMemo, useEffect, use, type ReactNode, type Dispatch } from 'react';
import type { ActiveSession } from '@/types';

// FIX Cortez31: AppState now contains only UI state, not user auth
interface AppState {
  currentSession: ActiveSession | null;
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
}

// FIX Cortez31: Removed SET_USER action - use AuthContext for user state
type AppAction =
  | { type: 'SET_SESSION'; payload: ActiveSession | null }
  | { type: 'TOGGLE_THEME' }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'RESET_STATE' };

const initialState: AppState = {
  currentSession: null,
  theme: 'light',
  sidebarCollapsed: false
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_SESSION':
      return { ...state, currentSession: action.payload };

    case 'TOGGLE_THEME':
      return { ...state, theme: state.theme === 'light' ? 'dark' : 'light' };

    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };

    case 'RESET_STATE':
      return initialState;

    default:
      return state;
  }
}

// FIX Cortez31: Removed setUser action - use AuthContext for user management
interface AppContextType {
  state: AppState;
  dispatch: Dispatch<AppAction>;
  actions: {
    setSession: (session: ActiveSession | null) => void;
    toggleTheme: () => void;
    toggleSidebar: () => void;
    resetState: () => void;
  };
}

// React 19: Context with null default
const AppContext = createContext<AppContextType | null>(null);

/**
 * useApp - React 19 Custom Hook
 *
 * Uses the new React 19 `use()` hook for reading context.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useApp(): AppContextType {
  const context = use(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
}

// React 19: Export context for direct use() calls if needed
export { AppContext };

// React 19: Function component without React.FC
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState, (initial) => {
    // Cargar estado desde localStorage
    if (typeof window === 'undefined') return initial;

    try {
      const savedTheme = localStorage.getItem('theme');
      const savedSidebarState = localStorage.getItem('sidebarCollapsed');

      return {
        ...initial,
        theme: (savedTheme as 'light' | 'dark') || initial.theme,
        sidebarCollapsed: savedSidebarState === 'true'
      };
    } catch (error) {
      console.warn('Failed to load state from localStorage:', error);
      return initial;
    }
  });

  // Persistir cambios en localStorage
  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem('theme', state.theme);
      localStorage.setItem('sidebarCollapsed', String(state.sidebarCollapsed));
    } catch (error) {
      console.warn('Failed to save state to localStorage:', error);
    }
  }, [state.theme, state.sidebarCollapsed]);

  // Aplicar tema al documento
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', state.theme);
  }, [state.theme]);

  // FIX Cortez31: Memoized actions - removed setUser and logout (use AuthContext)
  const actions = useMemo(() => ({
    setSession: (session: ActiveSession | null) => {
      dispatch({ type: 'SET_SESSION', payload: session });
    },

    toggleTheme: () => {
      dispatch({ type: 'TOGGLE_THEME' });
    },

    toggleSidebar: () => {
      dispatch({ type: 'TOGGLE_SIDEBAR' });
    },

    resetState: () => {
      // FIX Cortez31: Only reset UI state, not auth tokens (AuthContext handles that)
      dispatch({ type: 'RESET_STATE' });
    }
  }), []);

  const value = useMemo(
    () => ({ state, dispatch, actions }),
    [state, actions]
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
