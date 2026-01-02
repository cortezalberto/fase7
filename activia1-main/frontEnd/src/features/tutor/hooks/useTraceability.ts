/**
 * useTraceability Hook - Traceability N4 management
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { tracesService } from '@/services/api';
import type { TraceabilityN4 } from '@/types';

// API Error type
interface ApiError {
  error?: {
    message?: string;
  };
  message?: string;
}

export interface UseTraceabilityOptions {
  onError?: (message: string) => void;
}

export interface UseTraceabilityReturn {
  // State
  traceData: TraceabilityN4 | null;
  isLoading: boolean;
  showModal: boolean;

  // Actions
  fetchTraceability: (traceId: string) => Promise<void>;
  openModal: () => void;
  closeModal: () => void;
}

export function useTraceability({
  onError,
}: UseTraceabilityOptions): UseTraceabilityReturn {
  const [traceData, setTraceData] = useState<TraceabilityN4 | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const isMountedRef = useRef<boolean>(true);

  // Fetch traceability data
  const fetchTraceability = useCallback(
    async (traceId: string) => {
      if (!traceId) {
        onError?.('No hay trace_id disponible. Envía un mensaje primero.');
        return;
      }

      setIsLoading(true);
      try {
        const data = await tracesService.getN4(traceId);

        if (!isMountedRef.current) return;

        setTraceData(data);
        setShowModal(true);
      } catch (error: unknown) {
        if (!isMountedRef.current) return;

        if (import.meta.env.DEV) {
          console.error('Error fetching traceability:', error);
        }

        const err = error as ApiError;
        const errorMsg = err.error?.message || err.message || 'Error desconocido';
        onError?.(`Error al obtener trazabilidad: ${errorMsg}`);
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      }
    },
    [onError]
  );

  // Open modal
  const openModal = useCallback(() => {
    setShowModal(true);
  }, []);

  // Close modal
  const closeModal = useCallback(() => {
    setShowModal(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    traceData,
    isLoading,
    showModal,
    fetchTraceability,
    openModal,
    closeModal,
  };
}
