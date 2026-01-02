/**
 * ChatMessage Component
 * FIX Cortez31: Reusable chat message bubble component
 *
 * Used by TutorPage and SimulatorsPage to display conversation messages
 */
import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Sparkles, AlertCircle } from 'lucide-react';

export interface ChatMessageData {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    agent_used?: string;
    cognitive_state?: string;
    ai_involvement?: number;
    blocked?: boolean;
    block_reason?: string;
    risks_detected?: string[];
    simulator_type?: string;
  };
}

interface ChatMessageProps {
  message: ChatMessageData;
  /** Show agent name in header */
  agentName?: string;
  /** Custom icon for assistant messages */
  assistantIcon?: React.ReactNode;
  /** Show metadata badges */
  showMetadata?: boolean;
  /** Custom gradient for user messages */
  userGradient?: string;
  /** Custom background for assistant messages */
  assistantBg?: string;
}

/**
 * Reusable chat message bubble
 *
 * @example
 * <ChatMessage
 *   message={msg}
 *   agentName="Tutor IA"
 *   showMetadata
 * />
 *
 * @example
 * // For simulators
 * <ChatMessage
 *   message={msg}
 *   agentName={simulator.name}
 *   assistantIcon={<SimulatorIcon />}
 *   userGradient="from-green-500 to-emerald-600"
 * />
 */
// FIX Cortez48: Use function component pattern instead of React.FC
export function ChatMessage({
  message,
  agentName = 'Asistente',
  assistantIcon,
  showMetadata = true,
  userGradient = 'from-indigo-500 to-purple-600',
  assistantBg = 'bg-[var(--bg-tertiary)]',
}: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-full text-sm text-[var(--text-muted)]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] ${
          isUser
            ? `bg-gradient-to-br ${userGradient} text-white rounded-2xl rounded-br-md`
            : `${assistantBg} text-[var(--text-primary)] rounded-2xl rounded-bl-md`
        } px-5 py-4 animate-slideIn`}
      >
        {/* Assistant header */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-[var(--border-color)]">
            {assistantIcon || <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />}
            <span className="text-sm font-medium text-[var(--accent-primary)]">
              {agentName}
            </span>
            {showMetadata && message.metadata?.cognitive_state && (
              <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-[var(--accent-primary)]/10 text-[var(--accent-primary)]">
                {message.metadata.cognitive_state}
              </span>
            )}
          </div>
        )}

        {/* Message content */}
        <div className={`markdown-content ${isUser ? 'text-white' : ''}`}>
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>

        {/* Risk alerts */}
        {showMetadata && message.metadata?.risks_detected && message.metadata.risks_detected.length > 0 && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-xs text-[var(--warning)]">
              <AlertCircle className="w-3 h-3" />
              <span>Riesgos detectados: {message.metadata.risks_detected.length}</span>
            </div>
          </div>
        )}

        {/* Blocked message indicator */}
        {showMetadata && message.metadata?.blocked && (
          <div className="mt-3 pt-3 border-t border-[var(--border-color)]">
            <div className="flex items-center gap-2 text-xs text-[var(--error)]">
              <AlertCircle className="w-3 h-3" />
              <span>{message.metadata.block_reason || 'Mensaje bloqueado por gobernanza'}</span>
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className={`mt-2 text-xs ${isUser ? 'text-white/60' : 'text-[var(--text-muted)]'}`}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};

/**
 * Typing indicator for chat
 */
// FIX Cortez48: Use function component pattern instead of React.FC
interface TypingIndicatorProps {
  agentName?: string;
  icon?: React.ReactNode;
}

export function TypingIndicator({ agentName = 'Asistente', icon }: TypingIndicatorProps) {
  return (
  <div className="flex justify-start">
    <div className="bg-[var(--bg-tertiary)] rounded-2xl rounded-bl-md px-5 py-4">
      <div className="flex items-center gap-2 mb-2">
        {icon || <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />}
        <span className="text-sm font-medium text-[var(--accent-primary)]">{agentName}</span>
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

/**
 * Simple message list wrapper with auto-scroll
 */
// FIX Cortez48: Use function component pattern instead of React.FC
interface ChatMessageListProps {
  messages: ChatMessageData[];
  agentName?: string;
  isLoading?: boolean;
  messagesEndRef?: React.RefObject<HTMLDivElement>;
}

export function ChatMessageList({ messages, agentName, isLoading, messagesEndRef }: ChatMessageListProps) {
  return (
  <div className="flex-1 overflow-y-auto p-6 space-y-6 chat-scroll">
    {messages.map((message) => (
      <ChatMessage key={message.id} message={message} agentName={agentName} />
    ))}
    {isLoading && <TypingIndicator agentName={agentName} />}
    <div ref={messagesEndRef} />
  </div>
  );
}

export default ChatMessage;
