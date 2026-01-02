/**
 * ChatMessageBubble Component - Individual chat message display
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import ReactMarkdown from 'react-markdown';
import { Sparkles, AlertCircle } from 'lucide-react';
import type { ChatMessage } from '@/types';

interface ChatMessageBubbleProps {
  message: ChatMessage;
}

export function ChatMessageBubble({ message }: ChatMessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] ${
          isUser
            ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white rounded-2xl rounded-br-md'
            : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-2xl rounded-bl-md'
        } px-5 py-4 animate-slideIn`}
      >
        {!isUser && (
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-color)]">
            <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />
            <span className="text-sm font-medium text-[var(--accent-primary)]">
              Tutor IA
            </span>
            {message.metadata?.cognitive_state && (
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]">
                {message.metadata.cognitive_state}
              </span>
            )}
          </div>
        )}

        <div className={`markdown-content ${isUser ? 'text-white' : ''}`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {message.metadata?.risks_detected && message.metadata.risks_detected.length > 0 && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-xs text-[var(--warning)]">
              <AlertCircle className="w-3 h-3" />
              <span>Riesgos detectados: {message.metadata.risks_detected.length}</span>
            </div>
          </div>
        )}

        <div
          className={`mt-2 text-xs ${isUser ? 'text-white/60' : 'text-[var(--text-muted)]'}`}
        >
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
}
