/**
 * UI Store - Zustand store for UI state management
 * FIX Cortez31: Migrated from AppContext to Zustand for simpler state management
 *
 * Manages:
 * - Theme (light/dark)
 * - Sidebar collapsed state
 *
 * Features:
 * - Automatic localStorage persistence
 * - Type-safe selectors
 * - No provider wrapping needed
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

type Theme = 'light' | 'dark';

interface UIState {
  theme: Theme;
  sidebarCollapsed: boolean;
}

interface UIActions {
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  resetUI: () => void;
}

type UIStore = UIState & UIActions;

const initialState: UIState = {
  theme: 'light',
  sidebarCollapsed: false,
};

/**
 * UI Store with localStorage persistence
 *
 * @example
 * // In a component:
 * const theme = useUIStore(state => state.theme);
 * const toggleTheme = useUIStore(state => state.toggleTheme);
 *
 * // Or get multiple values:
 * const { theme, sidebarCollapsed } = useUIStore();
 */
export const useUIStore = create<UIStore>()(
  persist(
    (set, get) => ({
      // State
      ...initialState,

      // Actions
      setTheme: (theme: Theme) => {
        set({ theme });
        // Apply theme to document
        document.documentElement.setAttribute('data-theme', theme);
      },

      toggleTheme: () => {
        const newTheme = get().theme === 'light' ? 'dark' : 'light';
        set({ theme: newTheme });
        // Apply theme to document
        document.documentElement.setAttribute('data-theme', newTheme);
      },

      setSidebarCollapsed: (collapsed: boolean) => {
        set({ sidebarCollapsed: collapsed });
      },

      toggleSidebar: () => {
        set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed }));
      },

      resetUI: () => {
        set(initialState);
        document.documentElement.setAttribute('data-theme', initialState.theme);
      },
    }),
    {
      name: 'ui-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist these fields
      partialize: (state) => ({
        theme: state.theme,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
      // Apply theme on hydration
      onRehydrateStorage: () => (state) => {
        if (state?.theme) {
          document.documentElement.setAttribute('data-theme', state.theme);
        }
      },
    }
  )
);

// Selector hooks for better performance (avoid re-renders)
export const useTheme = () => useUIStore((state) => state.theme);
export const useSidebarCollapsed = () => useUIStore((state) => state.sidebarCollapsed);
export const useToggleTheme = () => useUIStore((state) => state.toggleTheme);
export const useToggleSidebar = () => useUIStore((state) => state.toggleSidebar);
