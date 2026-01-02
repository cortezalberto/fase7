/**
 * Zustand Stores - Central exports
 * FIX Cortez31: Migrated from Context-based state management to Zustand
 *
 * Stores:
 * - uiStore: Theme and sidebar state (persisted to localStorage)
 * - sessionStore: Current learning session state
 *
 * Benefits over Context:
 * - No provider wrapping needed
 * - Better performance (selective re-renders)
 * - Built-in persistence middleware
 * - Simpler API than useReducer + Context
 */

// UI Store - Theme and sidebar
export {
  useUIStore,
  useTheme,
  useSidebarCollapsed,
  useToggleTheme,
  useToggleSidebar,
} from './uiStore';

// Session Store - Current learning session
export {
  useSessionStore,
  useCurrentSession,
  useSetSession,
  useClearSession,
  useIsSessionActive,
  type ActiveSession,
} from './sessionStore';
