/**
 * useTutorSession Hook - Tutor session management
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { sessionsService, interactionsService } from '@/services/api';
import type { ChatMessage, Session, SessionMode } from '@/types';

// API Error type
interface ApiError {
  error?: {
    message?: string;
  };
  message?: string;
  code?: string;
}

// Get error message helper
const getErrorMessage = (err: unknown): string => {
  const error = err as ApiError;
  return error.error?.message || error.message || 'Error desconocido';
};

export interface UseTutorSessionOptions {
  userId: string;
  userName: string;
  onError?: (message: string) => void;
}

export interface UseTutorSessionReturn {
  // State
  session: Session | null;
  messages: ChatMessage[];
  isCreatingSession: boolean;
  isLoading: boolean;
  lastTraceId: string | null;

  // Actions
  initializeSession: () => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  resetSession: () => void;
  setInput: (value: string) => void;
  input: string;
}

export function useTutorSession({
  userId,
  userName,
  onError,
}: UseTutorSessionOptions): UseTutorSessionReturn {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [lastTraceId, setLastTraceId] = useState<string | null>(null);
  const [input, setInput] = useState('');

  const isMountedRef = useRef<boolean>(true);

  // Initialize session
  const initializeSession = useCallback(async () => {
    if (session) return;

    setIsCreatingSession(true);
    try {
      const newSession = await sessionsService.create({
        student_id: userId || 'guest',
        activity_id: 'general_learning',
        mode: 'TUTOR' as SessionMode,
      });

      if (!isMountedRef.current) return;

      setSession(newSession);

      // Welcome message
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `¡Hola ${userName || 'estudiante'}! 👋

Soy tu tutor de IA, diseñado para ayudarte a aprender programación de manera efectiva.

**¿Cómo funciono?**
- Te guío con preguntas para que descubras las soluciones por ti mismo
- No te doy respuestas directas, sino pistas y orientación
- Analizo tu proceso de pensamiento para ayudarte mejor

**¿Qué puedo hacer por ti hoy?**
- Explicar conceptos de programación
- Ayudarte con ejercicios
- Revisar tu código
- Resolver dudas técnicas

¿En qué te puedo ayudar?`,
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      if (!isMountedRef.current) return;

      if (import.meta.env.DEV) {
        console.error('Error creating session:', error);
      }
      onError?.('Error al crear la sesión. Intenta de nuevo.');
    } finally {
      if (isMountedRef.current) {
        setIsCreatingSession(false);
      }
    }
  }, [session, userId, userName, onError]);

  // Send message
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading || !session) return;

      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'user',
        content: content.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      setIsLoading(true);

      try {
        // Build conversation context (last 10 messages)
        const conversationHistory = messages.slice(-10).map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

        const interactionResult = await interactionsService.process({
          session_id: session.id,
          prompt: userMessage.content,
          context: {
            conversation_history: conversationHistory,
            message_count: messages.length,
          },
        });

        if (!isMountedRef.current) return;

        // Store trace_id for traceability analysis
        if (interactionResult.trace_id) {
          setLastTraceId(interactionResult.trace_id);
        }

        const aiMessage: ChatMessage = {
          id: interactionResult.interaction_id,
          role: 'assistant',
          content: interactionResult.response,
          timestamp: new Date(),
          metadata: {
            agent_used: interactionResult.agent_used,
            cognitive_state: interactionResult.cognitive_state_detected,
            ai_involvement: interactionResult.ai_involvement,
            blocked: interactionResult.blocked,
            block_reason: interactionResult.block_reason ?? undefined,
            risks_detected: interactionResult.risks_detected,
          },
        };

        setMessages((prev) => [...prev, aiMessage]);
      } catch (error: unknown) {
        if (!isMountedRef.current) return;

        const errorMessage: ChatMessage = {
          id: 'error-' + Date.now(),
          role: 'assistant',
          content: `Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta de nuevo.

*Error: ${getErrorMessage(error)}*`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      }
    },
    [isLoading, session, messages]
  );

  // Reset session
  const resetSession = useCallback(() => {
    setSession(null);
    setMessages([]);
    setLastTraceId(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    session,
    messages,
    isCreatingSession,
    isLoading,
    lastTraceId,
    initializeSession,
    sendMessage,
    resetSession,
    setInput,
    input,
  };
}
