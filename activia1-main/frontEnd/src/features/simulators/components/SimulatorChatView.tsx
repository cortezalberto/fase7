/**
 * SimulatorChatView Component - Active simulation chat interface
 *
 * Cortez43: Extracted from SimulatorsPage.tsx (514 lines)
 * Cortez92: Updated to handle ISO-8601 string timestamps
 */

import { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2, X, Users, type LucideIcon } from 'lucide-react';
import type { Simulator, ChatMessage } from '@/types';
import { simulatorIcons, simulatorColors } from '../config/simulatorConfig';

interface SimulatorChatViewProps {
  simulator: Simulator;
  messages: ChatMessage[];
  input: string;
  isSending: boolean;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onClose: () => void;
}

export function SimulatorChatView({
  simulator,
  messages,
  input,
  isSending,
  onInputChange,
  onSendMessage,
  onClose,
}: SimulatorChatViewProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const Icon: LucideIcon = simulatorIcons[simulator.type] || Users;
  const colorClass = simulatorColors[simulator.type] || 'from-gray-500 to-gray-600';

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <div
            className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClass} flex items-center justify-center`}
          >
            <Icon className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">{simulator.name}</h1>
            <p className="text-sm text-[var(--text-secondary)]">Simulación activa</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-red-500 transition-all"
        >
          <X className="w-4 h-4" />
          Terminar
        </button>
      </div>

      {/* Chat Area */}
      <div className="flex-1 bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6 space-y-4 chat-scroll">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] px-5 py-4 animate-slideIn ${
                  message.role === 'user'
                    ? `bg-gradient-to-br ${colorClass} text-white rounded-2xl rounded-br-md`
                    : 'bg-[var(--bg-tertiary)] text-[var(--text-primary)] rounded-2xl rounded-bl-md'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-color)]">
                    <Icon className="w-4 h-4 text-[var(--accent-primary)]" />
                    <span className="text-sm font-medium text-[var(--accent-primary)]">
                      {simulator.name.split(' ')[0]}
                    </span>
                  </div>
                )}
                <div className="markdown-content">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                <p
                  className={`text-xs mt-2 ${
                    message.role === 'user' ? 'text-white/60' : 'text-[var(--text-muted)]'
                  }`}
                >
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="flex justify-start">
              <div className="bg-[var(--bg-tertiary)] rounded-2xl rounded-bl-md px-5 py-4">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-[var(--border-color)] bg-[var(--bg-secondary)]">
          <div className="flex items-center gap-4">
            <input
              type="text"
              value={input}
              onChange={(e) => onInputChange(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && onSendMessage()}
              placeholder="Escribe tu respuesta..."
              className="flex-1 px-4 py-3 rounded-xl bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:outline-none transition-colors"
              disabled={isSending}
            />
            <button
              onClick={onSendMessage}
              disabled={!input.trim() || isSending}
              className={`h-12 w-12 rounded-xl bg-gradient-to-br ${colorClass} text-white flex items-center justify-center hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all`}
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Competencies */}
      <div className="mt-4 p-4 bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)]">
        <p className="text-sm text-[var(--text-muted)] mb-2">Competencias evaluadas:</p>
        <div className="flex flex-wrap gap-2">
          {simulator.competencies.map((comp) => (
            <span
              key={`${simulator.type}-comp-${comp}`}
              className="px-3 py-1 rounded-full text-xs bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
            >
              {comp.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
