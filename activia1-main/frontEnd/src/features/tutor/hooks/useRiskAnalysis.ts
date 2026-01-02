/**
 * useRiskAnalysis Hook - Risk analysis management
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { risksService } from '@/services/api';
import type { RiskAnalysis5D } from '@/types';

// API Error type
interface ApiError {
  error?: {
    message?: string;
  };
  message?: string;
  code?: string;
}

export interface UseRiskAnalysisOptions {
  sessionId: string | null;
  onError?: (message: string, duration?: number) => void;
}

export interface UseRiskAnalysisReturn {
  // State
  riskData: RiskAnalysis5D | null;
  isLoading: boolean;
  showRiskPanel: boolean;
  showRiskModal: boolean;

  // Actions
  analyzeRisks: (silent?: boolean) => Promise<void>;
  toggleRiskPanel: () => void;
  openRiskModal: () => void;
  closeRiskModal: () => void;
}

export function useRiskAnalysis({
  sessionId,
  onError,
}: UseRiskAnalysisOptions): UseRiskAnalysisReturn {
  const [riskData, setRiskData] = useState<RiskAnalysis5D | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showRiskPanel, setShowRiskPanel] = useState(true);
  const [showRiskModal, setShowRiskModal] = useState(false);

  const isMountedRef = useRef<boolean>(true);

  // Analyze risks
  const analyzeRisks = useCallback(
    async (silent: boolean = false) => {
      if (!sessionId) {
        if (!silent) {
          onError?.('No hay sesión activa. Inicia una conversación primero.');
        }
        return;
      }

      setIsLoading(true);
      try {
        const data = await risksService.analyze5D(sessionId);

        if (!isMountedRef.current) return;

        setRiskData({
          session_id: data.session_id,
          overall_score: data.overall_score,
          risk_level: data.risk_level as RiskAnalysis5D['risk_level'],
          dimensions: data.dimensions as RiskAnalysis5D['dimensions'],
          top_risks: data.top_risks as RiskAnalysis5D['top_risks'],
          recommendations: data.recommendations,
        });

        if (!silent) {
          setShowRiskModal(true);
        }
      } catch (error: unknown) {
        if (!isMountedRef.current) return;

        if (!silent) {
          if (import.meta.env.DEV) {
            console.error('Error analyzing risks:', error);
          }

          const err = error as ApiError;
          const errorMsg = err.error?.message || err.message || 'Error desconocido';

          if (err.code === 'ECONNABORTED') {
            onError?.(
              'El análisis está tomando demasiado tiempo. Verifica que Ollama esté corriendo.',
              8000
            );
          } else if (err.message === 'Network Error') {
            onError?.(
              'Error de conexión. Verifica que el backend y Ollama estén activos.',
              8000
            );
          } else {
            onError?.(`Error al analizar riesgos: ${errorMsg}`);
          }
        }
      } finally {
        if (isMountedRef.current) {
          setIsLoading(false);
        }
      }
    },
    [sessionId, onError]
  );

  // Toggle risk panel visibility
  const toggleRiskPanel = useCallback(() => {
    setShowRiskPanel((prev) => !prev);
  }, []);

  // Open risk modal
  const openRiskModal = useCallback(() => {
    setShowRiskModal(true);
  }, []);

  // Close risk modal
  const closeRiskModal = useCallback(() => {
    setShowRiskModal(false);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return {
    riskData,
    isLoading,
    showRiskPanel,
    showRiskModal,
    analyzeRisks,
    toggleRiskPanel,
    openRiskModal,
    closeRiskModal,
  };
}
