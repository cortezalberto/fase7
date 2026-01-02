/**
 * ChatInput Component - Message input with keyboard shortcuts
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import React, { useRef, useEffect } from 'react';
import { Send, Loader2, Info, Clock } from 'lucide-react';

interface ChatInputProps {
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
  isDisabled: boolean;
  sessionId?: string;
}

export function ChatInput({
  input,
  onInputChange,
  onSubmit,
  isLoading,
  isDisabled,
  sessionId,
}: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Focus input after loading completes
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className="p-4 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
      <form onSubmit={handleSubmit} className="flex items-end gap-4">
        <div className="flex-1 relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu pregunta o comparte tu código..."
            rows={1}
            className="w-full px-4 py-3 pr-12 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:outline-none resize-none transition-all"
            style={{ minHeight: '48px', maxHeight: '200px' }}
            disabled={isDisabled || isLoading}
          />
        </div>
        <button
          type="submit"
          disabled={!input.trim() || isLoading || isDisabled}
          className="h-12 w-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>

      {/* Quick Tips */}
      <div className="flex items-center gap-4 mt-3 text-xs text-[var(--text-muted)]">
        <div className="flex items-center gap-1">
          <Info className="w-3 h-3" />
          <span>Enter para enviar, Shift+Enter para nueva línea</span>
        </div>
        {sessionId && (
          <div className="flex items-center gap-1 ml-auto">
            <Clock className="w-3 h-3" />
            <span>Sesión: {sessionId.slice(0, 8)}...</span>
          </div>
        )}
      </div>
    </div>
  );
}
