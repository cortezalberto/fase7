/**
 * Training Service - Entrenador Digital
 *
 * Cortez55: Refactorizado para integrar con backend V2 (Cortez50)
 *
 * Maneja:
 * - Obtención de materias y temas disponibles
 * - Inicio de sesiones de entrenamiento
 * - Solicitud de pistas (V1 legacy y V2 contextual)
 * - Envío de código para evaluación (V1 y V2 con trazabilidad)
 * - Captura de reflexiones post-ejercicio
 * - Análisis de proceso cognitivo
 * - Estado de sesiones activas
 */

import apiClient from './client';

// ============================================================================
// ENUMS (Cortez50 - N4 Traceability)
// ============================================================================

/** Estados cognitivos inferidos durante entrenamiento */
export enum CognitiveStateEnum {
  INICIO = 'inicio',
  EXPLORACION = 'exploracion',
  IMPLEMENTACION = 'implementacion',
  DEPURACION = 'depuracion',
  DEPURACION_SINTAXIS = 'depuracion_sintaxis',
  CAMBIO_ESTRATEGIA = 'cambio_estrategia',
  VALIDACION = 'validacion',
  ESTANCAMIENTO = 'estancamiento',
  REFLEXION = 'reflexion',
}

/** Niveles de ayuda para pistas */
export enum HelpLevelEnum {
  MINIMO = 'minimo',
  BAJO = 'bajo',
  MEDIO = 'medio',
  ALTO = 'alto',
}

/** Tipos de riesgo detectables */
export enum RiskTypeEnum {
  COPY_PASTE = 'copy_paste',
  FRUSTRATION = 'frustration',
  HINT_DEPENDENCY = 'hint_dependency',
  RAPID_SUBMISSION = 'rapid_submission',
  TIME_PRESSURE = 'time_pressure',
  COGNITIVE_OVERLOAD = 'cognitive_overload',
}

/** Severidad de riesgos */
export enum RiskSeverityEnum {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// ============================================================================
// TIPOS / INTERFACES - V1 (Legacy)
// ============================================================================

export interface EjercicioInfo {
  id: string;
  titulo: string;
  dificultad: string;
  tiempo_estimado_min: number;
  puntos: number;
}

export interface LeccionInfo {
  id: string;
  nombre: string;
  descripcion: string;
  unit_number: number;
  ejercicios: EjercicioInfo[];
  total_puntos: number;
  dificultad: string;
}

export interface LenguajeInfo {
  language: string;
  nombre_completo: string;
  lecciones: LeccionInfo[];
}

// LEGACY TYPES (mantener para compatibilidad)
export interface TemaInfo {
  id: string;
  nombre: string;
  descripcion: string;
  dificultad: string;
  tiempo_estimado_min: number;
}

export interface MateriaInfo {
  materia: string;
  codigo: string;
  temas: TemaInfo[];
}

export interface IniciarEntrenamientoRequest {
  language: string;
  unit_number: number;
  exercise_id?: string; // Opcional: ID de ejercicio específico
}

export interface EjercicioActual {
  numero: number;
  consigna: string;
  codigo_inicial: string;
}

export interface SesionEntrenamiento {
  session_id: string;
  materia: string;
  tema: string;
  ejercicio_actual: EjercicioActual;
  total_ejercicios: number;
  ejercicios_completados: number;
  tiempo_limite_min: number;
  inicio: string;
  fin_estimado: string;
}

export interface SolicitarPistaRequest {
  session_id: string;
  numero_pista: number;
}

export interface PistaResponse {
  contenido: string;
  numero: number;
  total_pistas: number;
}

export interface CorreccionIARequest {
  session_id: string;
  codigo_usuario: string;
}

/**
 * Cortez56: Respuesta completa de corrección con IA
 * Incluye análisis, sugerencias y métricas de evaluación
 */
export interface CorreccionIAResponse {
  analisis: string;
  sugerencias: string[];
  codigo_corregido?: string;
  // Cortez56: Campos adicionales
  porcentaje: number;
  aprobado: boolean;
  tiempo_usado_min: number;
  resultados_detalle: ResultadoEjercicio[];
}

export interface SubmitEjercicioRequest {
  session_id: string;
  codigo_usuario: string;
}

export interface ResultadoEjercicio {
  numero: number;
  correcto: boolean;
  tests_pasados: number;
  tests_totales: number;
  mensaje: string;
}

export interface ResultadoFinal {
  session_id: string;
  nota_final: number;
  ejercicios_correctos: number;
  total_ejercicios: number;
  porcentaje: number;
  aprobado: boolean;
  tiempo_usado_min: number;
  resultados_detalle: ResultadoEjercicio[];
}

/**
 * Cortez56: Respuesta de submit ejercicio V1
 * Estructura plana (no anidada en "resultado")
 */
export interface SubmitEjercicioResponse {
  correcto: boolean;
  tests_pasados: number;
  tests_totales: number;
  mensaje: string;
  siguiente_ejercicio?: EjercicioActual;
  resultado_final?: ResultadoFinal;
}

export interface EstadoSesion {
  session_id: string;
  finalizado: boolean;
  tiempo_transcurrido_min: number;
  tiempo_restante_min: number;
  pistas_usadas: number;
  penalizacion_actual: number;
  pistas_disponibles: number;
}

// ============================================================================
// TIPOS / INTERFACES - V2 (Cortez50 - N4 Traceability)
// ============================================================================

/** Request para pista contextual con T-IA-Cog */
export interface SolicitarPistaV2Request {
  session_id: string;
  numero_pista: number; // 1-4
  codigo_actual?: string;
  ultimo_error?: string;
}

/** Respuesta con pista contextual de T-IA-Cog */
export interface PistaV2Response {
  contenido: string;
  numero: number;
  nivel_ayuda: HelpLevelEnum;
  total_pistas: number;
  requiere_reflexion: boolean;
  pregunta_seguimiento?: string;
  metadata: Record<string, unknown>;
}

/** Request para capturar reflexión post-ejercicio */
export interface ReflexionRequest {
  session_id: string;
  exercise_id: string;
  que_fue_dificil: string;
  como_lo_resolvi: string;
  que_aprendi: string;
  alternativas_consideradas?: string;
  errores_cometidos?: string;
}

/** Respuesta a la captura de reflexión */
export interface ReflexionResponse {
  trace_id: string;
  mensaje: string;
  dimension_cognitiva_inferida: string;
  nivel_metacognitivo: string;
  xp_bonus: number;
}

/** Resumen de una traza cognitiva */
export interface TraceResumen {
  timestamp: string;
  tipo: string;
  estado_cognitivo: CognitiveStateEnum;
  confianza_inferencia: string;
  metadata: Record<string, unknown>;
}

/** Flag de riesgo detectado */
export interface RiskFlag {
  tipo: RiskTypeEnum;
  severidad: RiskSeverityEnum;
  mensaje: string;
  detectado_en: string;
  resuelto: boolean;
}

/** Análisis del proceso cognitivo de una sesión */
export interface ProcesoAnalisis {
  session_id: string;
  student_id: string;
  total_trazas: number;
  trazas_resumen: TraceResumen[];
  estados_mas_frecuentes: string[];
  transiciones_cognitivas: number;
  cambios_estrategia: number;
  tiempo_por_estado: Record<string, number>;
  riesgos_detectados: RiskFlag[];
  indice_autonomia: number; // 0-1
  indice_reflexion: number; // 0-1
  recomendaciones: string[];
}

/** Request para análisis de proceso */
export interface ProcesoRequest {
  incluir_trazas?: boolean;
  incluir_riesgos?: boolean;
  incluir_recomendaciones?: boolean;
}

/** Resultado de ejercicio con datos de trazabilidad */
export interface ResultadoEjercicioExtendido extends ResultadoEjercicio {
  intentos_realizados: number;
  pistas_solicitadas: number;
  tiempo_ejercicio_segundos: number;
  estado_cognitivo_final?: CognitiveStateEnum;
  riesgos_detectados: string[];
  trace_ids: string[];
}

/** Resultado final con métricas de proceso */
export interface ResultadoFinalExtendido {
  session_id: string;
  nota_final: number;
  ejercicios_correctos: number;
  total_ejercicios: number;
  porcentaje: number;
  aprobado: boolean;
  tiempo_usado_min: number;
  resultados_detalle: ResultadoEjercicioExtendido[];
  metricas_proceso?: Record<string, unknown>;
  indice_autonomia?: number;
  reflexiones_capturadas: number;
  trace_sequence_id?: string;
}

/** Request para enviar código con contexto V2 */
export interface SubmitEjercicioV2Request {
  session_id: string;
  codigo_usuario: string;
  tiempo_desde_ultimo_ms?: number;
  es_codigo_pegado?: boolean;
}

/** Respuesta V2 con datos de trazabilidad */
export interface SubmitEjercicioV2Response {
  correcto: boolean;
  tests_pasados: number;
  tests_totales: number;
  mensaje: string;
  siguiente_ejercicio?: EjercicioActual;
  finalizado: boolean;
  resultado_final?: ResultadoFinalExtendido;
  trace_id?: string;
  estado_cognitivo_inferido?: CognitiveStateEnum;
  riesgos_activos: RiskFlag[];
}

/** Sesión de entrenamiento extendida con soporte V2 */
export interface SesionEntrenamientoExtendida extends SesionEntrenamiento {
  trace_sequence_id?: string;
  pistas_disponibles: number;
  pistas_usadas: number;
  intentos_ejercicio_actual: number;
  estado_cognitivo_actual?: CognitiveStateEnum;
  riesgos_activos: string[];
  feature_flags: Record<string, boolean>;
}

// ============================================================================
// SERVICIO
// ============================================================================

export const trainingService = {
  // ==========================================================================
  // V1 ENDPOINTS (Legacy - compatibilidad)
  // ==========================================================================

  /**
   * Obtiene los lenguajes disponibles con sus lecciones
   * Estructura jerárquica: Lenguaje → Lecciones → Ejercicios
   */
  async getLenguajes(): Promise<LenguajeInfo[]> {
    const response = await apiClient.get<LenguajeInfo[]>('/training/lenguajes');
    return response.data;
  },

  /**
   * Obtiene las materias disponibles con sus temas (LEGACY)
   * @deprecated Usar getLenguajes() para la nueva estructura
   */
  async getMaterias(): Promise<MateriaInfo[]> {
    const response = await apiClient.get<MateriaInfo[]>('/training/materias');
    return response.data;
  },

  /**
   * Inicia una nueva sesión de entrenamiento
   */
  async iniciarEntrenamiento(
    request: IniciarEntrenamientoRequest
  ): Promise<SesionEntrenamiento> {
    const response = await apiClient.post<SesionEntrenamiento>(
      '/training/iniciar',
      request
    );
    return response.data;
  },

  /**
   * Envía el código de un ejercicio para evaluación (V1)
   * Retorna el resultado y el siguiente ejercicio si hay más
   */
  async submitEjercicio(
    request: SubmitEjercicioRequest
  ): Promise<SubmitEjercicioResponse> {
    const response = await apiClient.post<SubmitEjercicioResponse>(
      '/training/submit-ejercicio',
      request
    );
    return response.data;
  },

  /**
   * Solicita una pista para el ejercicio actual (V1 - estática)
   */
  async solicitarPista(request: SolicitarPistaRequest): Promise<PistaResponse> {
    const response = await apiClient.post<PistaResponse>(
      '/training/pista',
      request
    );
    return response.data;
  },

  /**
   * Solicita corrección con IA para el código actual
   */
  async corregirConIA(
    request: CorreccionIARequest
  ): Promise<CorreccionIAResponse> {
    const response = await apiClient.post<CorreccionIAResponse>(
      '/training/corregir-ia',
      request
    );
    return response.data;
  },

  // ==========================================================================
  // V2 ENDPOINTS (Cortez50 - N4 Traceability & T-IA-Cog Integration)
  // ==========================================================================

  /**
   * Solicita una pista contextual con T-IA-Cog (V2)
   * Genera pistas dinámicas basadas en el contexto del estudiante
   */
  async solicitarPistaV2(
    request: SolicitarPistaV2Request
  ): Promise<PistaV2Response> {
    const response = await apiClient.post<PistaV2Response>(
      '/training/pista/v2',
      request
    );
    return response.data;
  },

  /**
   * Captura reflexión post-ejercicio para trazabilidad N4
   * Registra el proceso metacognitivo del estudiante
   */
  async capturarReflexion(
    request: ReflexionRequest
  ): Promise<ReflexionResponse> {
    const response = await apiClient.post<ReflexionResponse>(
      '/training/reflexion',
      request
    );
    return response.data;
  },

  /**
   * Obtiene análisis del proceso cognitivo de una sesión
   * Incluye trazas, riesgos y recomendaciones
   */
  async obtenerProcesoAnalisis(
    sessionId: string,
    options?: ProcesoRequest
  ): Promise<ProcesoAnalisis> {
    const response = await apiClient.post<ProcesoAnalisis>(
      `/training/sesion/${sessionId}/proceso`,
      options || {}
    );
    return response.data;
  },

  /**
   * Envía código con contexto adicional para mejor trazabilidad (V2)
   * Detecta copy-paste, mide tiempos, infiere estados cognitivos
   */
  async submitEjercicioV2(
    request: SubmitEjercicioV2Request
  ): Promise<SubmitEjercicioV2Response> {
    const response = await apiClient.post<SubmitEjercicioV2Response>(
      '/training/submit/v2',
      request
    );
    return response.data;
  },

  /**
   * Cortez56: Obtiene el estado actual de una sesión de entrenamiento
   * Retorna información extendida con campos N4 de trazabilidad
   */
  async obtenerEstadoSesion(sessionId: string): Promise<SesionEntrenamientoExtendida> {
    const response = await apiClient.get<SesionEntrenamientoExtendida>(
      `/training/sesion/${sessionId}/estado`
    );
    return response.data;
  },

  /**
   * Cortez56: Obtiene estado básico de sesión (legacy)
   * @deprecated Usar obtenerEstadoSesion() para datos completos
   */
  async obtenerEstadoSesionLegacy(sessionId: string): Promise<EstadoSesion> {
    const response = await apiClient.get<EstadoSesion>(
      `/training/sesion/${sessionId}/estado`
    );
    return response.data;
  },
};
