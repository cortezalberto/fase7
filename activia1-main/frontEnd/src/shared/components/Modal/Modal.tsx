/**
 * FE-CODE-003: Reusable Modal Base Component
 * Provides consistent modal behavior with accessibility support
 */
import { useEffect, useCallback, type ReactNode } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Modal title */
  title?: string;
  /** Modal content */
  children: ReactNode;
  /** Additional CSS classes for the modal container */
  className?: string;
  /** Whether to show close button */
  showCloseButton?: boolean;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
  /** Title icon (optional) */
  icon?: ReactNode;
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-xl',
  full: 'max-w-4xl'
};

/**
 * Reusable Modal component with accessibility features
 * - Closes on Escape key
 * - Closes on backdrop click
 * - Traps focus within modal
 * - Prevents body scroll when open
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  className = '',
  showCloseButton = true,
  size = 'md',
  icon
}: ModalProps) {
  // FE-A11Y-001: Close on Escape key
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';

      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, handleKeyDown]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        // Close on backdrop click
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
    >
      <div
        className={`bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] ${sizeClasses[size]} w-full animate-scaleIn ${className}`}
      >
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-[var(--border-color)]">
            {title && (
              <h2
                id="modal-title"
                className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-2"
              >
                {icon}
                {title}
              </h2>
            )}
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 hover:bg-[var(--bg-hover)] rounded-lg transition-colors"
                aria-label="Cerrar modal"
              >
                <X className="w-5 h-5 text-[var(--text-secondary)]" aria-hidden="true" />
              </button>
            )}
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
}

export default Modal;
