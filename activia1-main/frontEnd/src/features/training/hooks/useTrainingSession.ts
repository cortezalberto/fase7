/**
 * useTrainingSession Hook - Training session management
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 * Cortez55: Extended with V2 support (N4 traceability, contextual hints)
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  trainingService,
  SesionEntrenamiento,
  // SesionEntrenamientoExtendida - Reserved for V2 training features
  ResultadoFinal,
  ResultadoEjercicio,
  EjercicioActual,
  SubmitEjercicioResponse,
  PistaResponse,
  // V2 types
  PistaV2Response,
  SubmitEjercicioV2Response,
  RiskFlag,
  CognitiveStateEnum,
  RiskTypeEnum,
  RiskSeverityEnum,
  ReflexionRequest,
  ReflexionResponse,
  ProcesoAnalisis,
  // Cortez56: Corrección IA
  CorreccionIAResponse,
} from '@/services/api';

// API Error type
interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

// Extract error message from API error
const getErrorMessage = (err: unknown): string => {
  const error = err as ApiError;
  return error.response?.data?.detail || error.message || 'Error desconocido';
};

export interface TrainingSessionParams {
  language: string;
  unit_number: number;
  exercise_id?: string;
  useV2?: boolean; // Cortez55: Enable V2 endpoints with N4 traceability
}

export interface UseTrainingSessionReturn {
  // State
  session: SesionEntrenamiento | null;
  currentExercise: EjercicioActual | null;
  code: string;
  loading: boolean;
  submitting: boolean;
  error: string | null;
  completedExercises: number;
  finalResult: ResultadoFinal | null;
  lastResult: ResultadoEjercicio | null;
  showExerciseResult: boolean;

  // Hints (V1)
  currentHint: PistaResponse | null;
  currentHintNumber: number;
  loadingHint: boolean;

  // V2 State (Cortez55)
  currentHintV2: PistaV2Response | null;
  cognitiveState: CognitiveStateEnum | null;
  activeRisks: RiskFlag[];
  lastTraceId: string | null;
  procesoAnalisis: ProcesoAnalisis | null;

  // Reflexion state (Cortez55)
  showReflexionModal: boolean;
  reflexionLoading: boolean;
  lastReflexionResponse: ReflexionResponse | null;

  // Cortez56: Corrección IA state
  correccionIA: CorreccionIAResponse | null;
  loadingCorreccion: boolean;
  showCorreccionModal: boolean;

  // Actions
  setCode: (code: string) => void;
  initSession: () => Promise<Date | null>;
  submitExercise: () => Promise<void>;
  requestHint: () => Promise<void>;
  requestHintV2: () => Promise<void>;
  resetSession: () => void;
  clearError: () => void;

  // V2 Actions (Cortez55)
  submitReflexion: (reflexion: Omit<ReflexionRequest, 'session_id' | 'exercise_id'>) => Promise<void>;
  loadProcesoAnalisis: () => Promise<void>;
  openReflexionModal: () => void;
  closeReflexionModal: () => void;

  // Cortez56: Corrección IA actions
  requestCorreccionIA: () => Promise<void>;
  openCorreccionModal: () => void;
  closeCorreccionModal: () => void;

  // Cortez56: Session state refresh
  refreshSessionState: () => Promise<void>;
}

export function useTrainingSession(params: TrainingSessionParams): UseTrainingSessionReturn {
  const { language, unit_number, exercise_id, useV2 = false } = params;

  // Session state
  const [session, setSession] = useState<SesionEntrenamiento | null>(null);
  const [currentExercise, setCurrentExercise] = useState<EjercicioActual | null>(null);
  const [code, setCodeState] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [completedExercises, setCompletedExercises] = useState<number>(0);
  const [finalResult, setFinalResult] = useState<ResultadoFinal | null>(null);
  const [lastResult, setLastResult] = useState<ResultadoEjercicio | null>(null);
  const [showExerciseResult, setShowExerciseResult] = useState<boolean>(false);

  // Hint state (V1)
  const [currentHint, setCurrentHint] = useState<PistaResponse | null>(null);
  const [currentHintNumber, setCurrentHintNumber] = useState<number>(0);
  const [loadingHint, setLoadingHint] = useState<boolean>(false);

  // V2 State (Cortez55)
  const [currentHintV2, setCurrentHintV2] = useState<PistaV2Response | null>(null);
  const [cognitiveState, setCognitiveState] = useState<CognitiveStateEnum | null>(null);
  const [activeRisks, setActiveRisks] = useState<RiskFlag[]>([]);
  const [lastTraceId, setLastTraceId] = useState<string | null>(null);
  const [procesoAnalisis, setProcesoAnalisis] = useState<ProcesoAnalisis | null>(null);

  // Reflexion state (Cortez55)
  const [showReflexionModal, setShowReflexionModal] = useState<boolean>(false);
  const [reflexionLoading, setReflexionLoading] = useState<boolean>(false);
  const [lastReflexionResponse, setLastReflexionResponse] = useState<ReflexionResponse | null>(null);

  // Cortez56: Corrección IA state
  const [correccionIA, setCorreccionIA] = useState<CorreccionIAResponse | null>(null);
  const [loadingCorreccion, setLoadingCorreccion] = useState<boolean>(false);
  const [showCorreccionModal, setShowCorreccionModal] = useState<boolean>(false);

  // Refs for cleanup and timing
  const isMountedRef = useRef<boolean>(true);
  const transitionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // V2 Refs for copy-paste detection and timing (Cortez55)
  const lastSubmitTimeRef = useRef<number>(Date.now());
  const codeChangeSourceRef = useRef<'typed' | 'pasted'>('typed');
  const previousCodeLengthRef = useRef<number>(0);

  // Detect paste events (Cortez55)
  const setCode = useCallback((newCode: string) => {
    // Detect if code was pasted (large change in single update)
    const lengthDiff = Math.abs(newCode.length - previousCodeLengthRef.current);
    if (lengthDiff > 50) {
      codeChangeSourceRef.current = 'pasted';
    } else {
      codeChangeSourceRef.current = 'typed';
    }
    previousCodeLengthRef.current = newCode.length;
    setCodeState(newCode);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Initialize session
  const initSession = useCallback(async (): Promise<Date | null> => {
    try {
      setLoading(true);
      setError(null);

      const data = await trainingService.iniciarEntrenamiento({
        language,
        unit_number,
        ...(exercise_id && { exercise_id }),
      });

      if (!isMountedRef.current) return null;

      setSession(data);
      setCurrentExercise(data.ejercicio_actual);
      setCodeState(data.ejercicio_actual.codigo_inicial);
      previousCodeLengthRef.current = data.ejercicio_actual.codigo_inicial.length;
      setCompletedExercises(data.ejercicios_completados);
      lastSubmitTimeRef.current = Date.now();

      return new Date(data.fin_estimado);
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error (redundant with error state)
      if (!isMountedRef.current) return null;
      setError(getErrorMessage(err));
      return null;
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  }, [language, unit_number, exercise_id]);

  // Submit exercise (V1 or V2 based on useV2 flag)
  const submitExercise = useCallback(async () => {
    if (!session || !code.trim()) return;

    try {
      setSubmitting(true);
      setError(null);

      const timeSinceLastSubmit = Date.now() - lastSubmitTimeRef.current;
      lastSubmitTimeRef.current = Date.now();

      if (useV2) {
        // V2 submission with traceability context
        const responseV2: SubmitEjercicioV2Response = await trainingService.submitEjercicioV2({
          session_id: session.session_id,
          codigo_usuario: code,
          tiempo_desde_ultimo_ms: timeSinceLastSubmit,
          es_codigo_pegado: codeChangeSourceRef.current === 'pasted',
        });

        if (!isMountedRef.current) return;

        // Update V2 state
        if (responseV2.trace_id) setLastTraceId(responseV2.trace_id);
        if (responseV2.estado_cognitivo_inferido) setCognitiveState(responseV2.estado_cognitivo_inferido);
        if (responseV2.riesgos_activos) setActiveRisks(responseV2.riesgos_activos);

        // Map V2 response to V1 format for UI compatibility
        const resultado: ResultadoEjercicio = {
          numero: currentExercise?.numero || 0,
          correcto: responseV2.correcto,
          tests_pasados: responseV2.tests_pasados,
          tests_totales: responseV2.tests_totales,
          mensaje: responseV2.mensaje,
        };

        setLastResult(resultado);
        setShowExerciseResult(true);

        if (transitionTimeoutRef.current) {
          clearTimeout(transitionTimeoutRef.current);
        }

        if (responseV2.siguiente_ejercicio) {
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;
            setCurrentExercise(responseV2.siguiente_ejercicio!);
            setCodeState(responseV2.siguiente_ejercicio!.codigo_inicial);
            previousCodeLengthRef.current = responseV2.siguiente_ejercicio!.codigo_inicial.length;
            setCompletedExercises((prev) => prev + 1);
            setShowExerciseResult(false);
            // Reset hints on exercise change
            setCurrentHint(null);
            setCurrentHintV2(null);
            setCurrentHintNumber(0);
            codeChangeSourceRef.current = 'typed';
          }, 2000);
        } else if (responseV2.finalizado && responseV2.resultado_final) {
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;
            // Convert extended result to base format for UI
            setFinalResult({
              session_id: responseV2.resultado_final!.session_id,
              nota_final: responseV2.resultado_final!.nota_final,
              ejercicios_correctos: responseV2.resultado_final!.ejercicios_correctos,
              total_ejercicios: responseV2.resultado_final!.total_ejercicios,
              porcentaje: responseV2.resultado_final!.porcentaje,
              aprobado: responseV2.resultado_final!.aprobado,
              tiempo_usado_min: responseV2.resultado_final!.tiempo_usado_min,
              resultados_detalle: responseV2.resultado_final!.resultados_detalle,
            });
          }, 2000);
        }
      } else {
        // V1 submission (Cortez56 - estructura plana)
        const response: SubmitEjercicioResponse = await trainingService.submitEjercicio({
          session_id: session.session_id,
          codigo_usuario: code,
        });

        if (!isMountedRef.current) return;

        // Cortez56: Construir ResultadoEjercicio desde respuesta plana
        const resultado: ResultadoEjercicio = {
          numero: currentExercise?.numero || 0,
          correcto: response.correcto,
          tests_pasados: response.tests_pasados,
          tests_totales: response.tests_totales,
          mensaje: response.mensaje,
        };

        setLastResult(resultado);
        setShowExerciseResult(true);

        if (transitionTimeoutRef.current) {
          clearTimeout(transitionTimeoutRef.current);
        }

        // Cortez56: Verificar si hay siguiente ejercicio
        if (response.siguiente_ejercicio) {
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;
            setCurrentExercise(response.siguiente_ejercicio!);
            setCodeState(response.siguiente_ejercicio!.codigo_inicial);
            previousCodeLengthRef.current = response.siguiente_ejercicio!.codigo_inicial.length;
            setCompletedExercises((prev) => prev + 1);
            setShowExerciseResult(false);
            setCurrentHint(null);
            setCurrentHintNumber(0);
          }, 2000);
        } else if (response.resultado_final) {
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;
            setFinalResult(response.resultado_final!);
          }, 2000);
        }
      }
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error
      if (!isMountedRef.current) return;
      setError(getErrorMessage(err));
    } finally {
      if (isMountedRef.current) {
        setSubmitting(false);
      }
    }
  }, [session, code, useV2, currentExercise]);

  // Request hint V1 (legacy - static hints)
  const requestHint = useCallback(async () => {
    if (!session) return;

    try {
      setLoadingHint(true);
      setError(null);

      const hint = await trainingService.solicitarPista({
        session_id: session.session_id,
        numero_pista: currentHintNumber,
      });

      if (!isMountedRef.current) return;

      setCurrentHint(hint);
      setCurrentHintNumber((prev) => prev + 1);
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error
      if (!isMountedRef.current) return;
      setError(getErrorMessage(err));
    } finally {
      if (isMountedRef.current) {
        setLoadingHint(false);
      }
    }
  }, [session, currentHintNumber]);

  // Request hint V2 (Cortez55 - contextual hints with T-IA-Cog)
  const requestHintV2 = useCallback(async () => {
    if (!session) return;

    try {
      setLoadingHint(true);
      setError(null);

      const hintV2 = await trainingService.solicitarPistaV2({
        session_id: session.session_id,
        numero_pista: currentHintNumber + 1, // V2 uses 1-4, not 0-3
        codigo_actual: code,
        ultimo_error: lastResult?.mensaje,
      });

      if (!isMountedRef.current) return;

      setCurrentHintV2(hintV2);
      setCurrentHintNumber((prev) => prev + 1);

      // Show reflexion modal if required by hint
      if (hintV2.requiere_reflexion) {
        setShowReflexionModal(true);
      }
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error
      if (!isMountedRef.current) return;
      setError(getErrorMessage(err));
    } finally {
      if (isMountedRef.current) {
        setLoadingHint(false);
      }
    }
  }, [session, currentHintNumber, code, lastResult]);

  // Submit reflexion (Cortez55)
  const submitReflexion = useCallback(
    async (reflexion: Omit<ReflexionRequest, 'session_id' | 'exercise_id'>) => {
      if (!session || !currentExercise) return;

      try {
        setReflexionLoading(true);
        setError(null);

        const response = await trainingService.capturarReflexion({
          session_id: session.session_id,
          exercise_id: `${currentExercise.numero}`,
          ...reflexion,
        });

        if (!isMountedRef.current) return;

        setLastReflexionResponse(response);
        setShowReflexionModal(false);
      } catch (err: unknown) {
        // FIX Cortez71: Removed DEV-only console.error
        if (!isMountedRef.current) return;
        setError(getErrorMessage(err));
      } finally {
        if (isMountedRef.current) {
          setReflexionLoading(false);
        }
      }
    },
    [session, currentExercise]
  );

  // Load proceso analisis (Cortez55)
  const loadProcesoAnalisis = useCallback(async () => {
    if (!session) return;

    try {
      setError(null);
      const analisis = await trainingService.obtenerProcesoAnalisis(session.session_id, {
        incluir_trazas: true,
        incluir_riesgos: true,
        incluir_recomendaciones: true,
      });

      if (!isMountedRef.current) return;

      setProcesoAnalisis(analisis);
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error
      if (!isMountedRef.current) return;
      setError(getErrorMessage(err));
    }
  }, [session]);

  // Modal controls
  const openReflexionModal = useCallback(() => {
    setShowReflexionModal(true);
  }, []);

  const closeReflexionModal = useCallback(() => {
    setShowReflexionModal(false);
  }, []);

  // Cortez56: Corrección IA modal controls
  const openCorreccionModal = useCallback(() => {
    setShowCorreccionModal(true);
  }, []);

  const closeCorreccionModal = useCallback(() => {
    setShowCorreccionModal(false);
  }, []);

  // Cortez56: Request AI correction
  const requestCorreccionIA = useCallback(async () => {
    if (!session || !code.trim()) return;

    try {
      setLoadingCorreccion(true);
      setError(null);

      const response = await trainingService.corregirConIA({
        session_id: session.session_id,
        codigo_usuario: code,
      });

      if (!isMountedRef.current) return;

      setCorreccionIA(response);
      setShowCorreccionModal(true);
    } catch (err: unknown) {
      // FIX Cortez71: Removed DEV-only console.error
      if (!isMountedRef.current) return;
      setError(getErrorMessage(err));
    } finally {
      if (isMountedRef.current) {
        setLoadingCorreccion(false);
      }
    }
  }, [session, code]);

  // Cortez56: Refresh session state from backend
  const refreshSessionState = useCallback(async () => {
    if (!session) return;

    try {
      const estadoExtendido = await trainingService.obtenerEstadoSesion(session.session_id);

      if (!isMountedRef.current) return;

      // Update session with extended data
      setSession({
        ...session,
        ejercicio_actual: estadoExtendido.ejercicio_actual,
        ejercicios_completados: estadoExtendido.ejercicios_completados,
      });
      setCurrentExercise(estadoExtendido.ejercicio_actual);

      // Update V2 fields if available
      if (estadoExtendido.estado_cognitivo_actual) {
        setCognitiveState(estadoExtendido.estado_cognitivo_actual);
      }
      if (estadoExtendido.riesgos_activos) {
        // Convert string[] to RiskFlag[] if needed
        setActiveRisks(estadoExtendido.riesgos_activos.map((r) => ({
          tipo: r as RiskTypeEnum,
          severidad: RiskSeverityEnum.LOW,
          mensaje: r,
          detectado_en: new Date().toISOString(),
          resuelto: false,
        })));
      }
    } catch {
      // FIX Cortez71: Removed DEV-only console.error
      // Don't set error for refresh failures - they're non-critical
    }
  }, [session]);

  // Reset session
  const resetSession = useCallback(() => {
    setFinalResult(null);
    setShowExerciseResult(false);
    setLastResult(null);
    setCurrentHint(null);
    setCurrentHintV2(null);
    setCurrentHintNumber(0);
    setError(null);
    setCognitiveState(null);
    setActiveRisks([]);
    setLastTraceId(null);
    setProcesoAnalisis(null);
    setLastReflexionResponse(null);
    // Cortez56: Reset IA correction state
    setCorreccionIA(null);
    setShowCorreccionModal(false);
    codeChangeSourceRef.current = 'typed';
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    isMountedRef.current = true;

    return () => {
      isMountedRef.current = false;
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, []);

  return {
    // V1 State
    session,
    currentExercise,
    code,
    loading,
    submitting,
    error,
    completedExercises,
    finalResult,
    lastResult,
    showExerciseResult,
    currentHint,
    currentHintNumber,
    loadingHint,

    // V2 State (Cortez55)
    currentHintV2,
    cognitiveState,
    activeRisks,
    lastTraceId,
    procesoAnalisis,
    showReflexionModal,
    reflexionLoading,
    lastReflexionResponse,

    // Cortez56: Corrección IA state
    correccionIA,
    loadingCorreccion,
    showCorreccionModal,

    // Actions
    setCode,
    initSession,
    submitExercise,
    requestHint,
    requestHintV2,
    resetSession,
    clearError,

    // V2 Actions (Cortez55)
    submitReflexion,
    loadProcesoAnalisis,
    openReflexionModal,
    closeReflexionModal,

    // Cortez56: Corrección IA actions
    requestCorreccionIA,
    openCorreccionModal,
    closeCorreccionModal,

    // Cortez56: Session state refresh
    refreshSessionState,
  };
}
