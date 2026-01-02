/**
 * useSimulatorSession Hook - Simulator session management
 *
 * Cortez43: Extracted from SimulatorsPage.tsx (514 lines)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { simulatorsService, sessionsService } from '@/services/api';
import type { Simulator, Session, ChatMessage, SessionMode } from '@/types';
import { welcomeMessages, defaultSimulators } from '../config/simulatorConfig';

export interface UseSimulatorSessionOptions {
  userId: string;
}

export interface UseSimulatorSessionReturn {
  // State
  simulators: Simulator[];
  isLoading: boolean;
  selectedSimulator: Simulator | null;
  session: Session | null;
  messages: ChatMessage[];
  input: string;
  isSending: boolean;

  // Actions
  setInput: (value: string) => void;
  startSimulation: (simulator: Simulator) => Promise<void>;
  sendMessage: () => Promise<void>;
  closeSimulation: () => void;
}

export function useSimulatorSession({
  userId,
}: UseSimulatorSessionOptions): UseSimulatorSessionReturn {
  const [simulators, setSimulators] = useState<Simulator[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedSimulator, setSelectedSimulator] = useState<Simulator | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);

  const isMountedRef = useRef<boolean>(true);

  // Fetch simulators on mount
  useEffect(() => {
    isMountedRef.current = true;
    const abortController = new AbortController();

    const fetchSimulators = async () => {
      try {
        const simulatorsList = await simulatorsService.getAllSimulators();

        if (!abortController.signal.aborted) {
          setSimulators(simulatorsList || []);
        }
      } catch (error) {
        if (!abortController.signal.aborted) {
          console.error('Error fetching simulators:', error);
          // Use mock data as fallback
          setSimulators(defaultSimulators as Simulator[]);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    fetchSimulators();

    return () => {
      isMountedRef.current = false;
      abortController.abort();
    };
  }, []);

  // Start simulation
  const startSimulation = useCallback(
    async (simulator: Simulator) => {
      setSelectedSimulator(simulator);
      setMessages([]);

      try {
        const newSession = await sessionsService.create({
          student_id: userId || 'guest',
          activity_id: `simulator_${simulator.type.toLowerCase()}`,
          mode: 'SIMULATOR' as SessionMode,
          simulator_type: simulator.type,
        });

        if (!isMountedRef.current) return;

        setSession(newSession);

        // Welcome message from simulator
        setMessages([
          {
            id: 'welcome',
            role: 'assistant',
            content:
              welcomeMessages[simulator.type] ||
              '¡Hola! Estoy listo para comenzar la simulación.',
            timestamp: new Date(),
          },
        ]);
      } catch (error) {
        if (!isMountedRef.current) return;
        console.error('Error creating session:', error);
      }
    },
    [userId]
  );

  // Send message
  const sendMessage = useCallback(async () => {
    if (!input.trim() || isSending || !session || !selectedSimulator) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsSending(true);

    try {
      // Build conversation context (last 10 messages)
      const conversationHistory = messages.slice(-10).map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const result = await simulatorsService.interact(session.id, {
        simulator_type: selectedSimulator.type,
        prompt: userMessage.content,
        context: {
          conversation_history: conversationHistory,
          message_count: messages.length,
        },
      });

      if (!isMountedRef.current) return;

      const aiMessage: ChatMessage = {
        id: Date.now().toString() + '-ai',
        role: 'assistant',
        content: result.response,
        timestamp: new Date(),
        metadata: {
          cognitive_state: 'simulator',
        },
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (error) {
      if (!isMountedRef.current) return;
      console.error('Error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: 'error',
          role: 'assistant',
          content: 'Lo siento, ocurrió un error. Por favor, intenta de nuevo.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      if (isMountedRef.current) {
        setIsSending(false);
      }
    }
  }, [input, isSending, session, selectedSimulator, messages]);

  // Close simulation
  const closeSimulation = useCallback(() => {
    setSelectedSimulator(null);
    setSession(null);
    setMessages([]);
  }, []);

  return {
    simulators,
    isLoading,
    selectedSimulator,
    session,
    messages,
    input,
    isSending,
    setInput,
    startSimulation,
    sendMessage,
    closeSimulation,
  };
}
