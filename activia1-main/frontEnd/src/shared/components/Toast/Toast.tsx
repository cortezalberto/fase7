/**
 * Sistema de Notificaciones Toast - React 19
 *
 * Migrated to React 19 with:
 * - New `use()` hook for context consumption
 * - Improved type safety with ReactNode
 * - Better component patterns
 */
import { createContext, useState, useCallback, useEffect, useRef, use, type ReactNode } from 'react';
import './Toast.css';

export type ToastType = 'info' | 'success' | 'warning' | 'error';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
  timestamp: number;
}

interface ToastContextType {
  toasts: Toast[];
  showToast: (message: string, type?: ToastType, duration?: number) => void;
  removeToast: (id: string) => void;
  clearAll: () => void;
}

// React 19: Context with null default for proper use() hook error handling
const ToastContext = createContext<ToastContextType | null>(null);

/**
 * useToast - React 19 Custom Hook
 *
 * Uses the new React 19 `use()` hook for reading context.
 */
// eslint-disable-next-line react-refresh/only-export-components
export const useToast = (): ToastContextType => {
  const context = use(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

// React 19: Export context for direct use() calls if needed
export { ToastContext };

// React 19: Using ReactNode type directly instead of React.ReactNode
export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  // FIX Cortez30: Track timeouts to prevent memory leaks
  const timeoutRefs = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  // FIX Cortez30: Cleanup all timeouts on unmount
  // FIX Cortez31: Capture ref value to avoid stale closure in cleanup
  useEffect(() => {
    const refs = timeoutRefs.current;
    return () => {
      refs.forEach(timeout => clearTimeout(timeout));
      refs.clear();
    };
  }, []);

  const removeToast = useCallback((id: string) => {
    // FIX Cortez30: Clear timeout when toast is manually removed
    const timeout = timeoutRefs.current.get(id);
    if (timeout) {
      clearTimeout(timeout);
      timeoutRefs.current.delete(id);
    }
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const showToast = useCallback((
    message: string,
    type: ToastType = 'info',
    duration: number = 5000
  ) => {
    const id = `toast_${Date.now()}_${Math.random()}`;
    const toast: Toast = {
      id,
      message,
      type,
      duration,
      timestamp: Date.now()
    };

    setToasts(prev => [...prev, toast]);

    // FIX Cortez30: Track timeout for cleanup
    if (duration > 0) {
      const timeout = setTimeout(() => {
        timeoutRefs.current.delete(id);
        removeToast(id);
      }, duration);
      timeoutRefs.current.set(id, timeout);
    }
  }, [removeToast]);

  const clearAll = useCallback(() => {
    // FIX Cortez30: Clear all timeouts when clearing all toasts
    timeoutRefs.current.forEach(timeout => clearTimeout(timeout));
    timeoutRefs.current.clear();
    setToasts([]);
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast, clearAll }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

// React 19: Function component without React.FC
function ToastContainer({
  toasts,
  onRemove
}: {
  toasts: Toast[];
  onRemove: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

// React 19: Function component without React.FC
function ToastItem({
  toast,
  onRemove
}: {
  toast: Toast;
  onRemove: (id: string) => void;
}) {
  const getIcon = () => {
    switch (toast.type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  return (
    <div className={`toast toast-${toast.type}`}>
      <div className="toast-icon">{getIcon()}</div>
      <div className="toast-message">{toast.message}</div>
      <button
        className="toast-close"
        onClick={() => onRemove(toast.id)}
        aria-label="Close"
      >
        ✕
      </button>
    </div>
  );
};
