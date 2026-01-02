/**
 * AuthContext - React 19 Migration
 *
 * React 19 introduces the `use()` hook which can read context values.
 * However, for backwards compatibility and custom error messages,
 * we maintain a custom useAuth() hook that uses `use()` internally.
 *
 * Key React 19 changes applied:
 * - Using `use()` hook for reading context (with fallback for undefined check)
 * - Improved typing with React 19 types
 * - Cleaner async patterns
 */
import { createContext, useState, useEffect, use, type ReactNode } from 'react';
import { User } from '../types';
// MIGRATED: Using new authService instead of legacy api
import { authService, User as AuthUser, RegisterRequest } from '../services/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
}

// React 19: Context with proper default for use() hook
const AuthContext = createContext<AuthContextType | null>(null);

// Helper to convert AuthUser to User type
const toUser = (authUser: AuthUser): User => ({
  id: authUser.id,
  username: authUser.username,
  email: authUser.email,
  full_name: authUser.full_name || undefined,
  roles: authUser.roles,
  is_active: authUser.is_active,
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // FIX Cortez30: Add isMounted check to prevent state updates after unmount
  useEffect(() => {
    let isMounted = true;

    const checkAuth = async () => {
      const token = authService.getAccessToken();
      if (token) {
        try {
          // First try to get from localStorage (faster)
          const cachedUser = authService.getCurrentUser();
          if (cachedUser) {
            if (isMounted) setUser(toUser(cachedUser));
          } else {
            // Fallback to fetching from backend
            const userData = await authService.getProfile();
            if (isMounted) setUser(toUser(userData));
          }
        } catch {
          authService.logout();
        }
      }
      if (isMounted) setIsLoading(false);
    };

    checkAuth();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = async (username: string, password: string) => {
    // authService expects email, but we receive username from form
    // The backend login endpoint accepts email field
    const response = await authService.login({ email: username, password });
    if (response.user) {
      setUser(toUser(response.user));
    }
  };

  const register = async (username: string, email: string, password: string, fullName?: string) => {
    // Construir payload con tipo correcto
    const payload: RegisterRequest = {
      username,
      email,
      password,
    };

    // Solo agregar full_name si NO está vacío
    if (fullName && fullName.trim() !== '') {
      payload.full_name = fullName.trim();
    }

    // Registrar y hacer auto-login guardando los tokens
    const result = await authService.register(payload, true);

    // Actualizar el estado del usuario si se hizo auto-login
    if (result.user) {
      setUser(toUser(result.user));
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth - React 19 Custom Hook
 *
 * Uses the new React 19 `use()` hook internally for reading context.
 * Maintains backwards compatibility with existing code.
 *
 * Note: In React 19, you can also use `use(AuthContext)` directly in components,
 * but this hook provides better error messages and type safety.
 */
// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextType {
  const context = use(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// React 19: Export context for direct use() calls if needed
export { AuthContext };
