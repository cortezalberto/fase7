/**
 * TypingIndicator Component - AI typing animation
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import { Sparkles } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="bg-[var(--bg-tertiary)] rounded-2xl rounded-bl-md px-5 py-4">
        <div className="flex items-center gap-2 mb-2">
          <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />
          <span className="text-sm font-medium text-[var(--accent-primary)]">Tutor IA</span>
        </div>
        <div className="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>
  );
}
