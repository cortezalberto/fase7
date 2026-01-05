/**
 * StudentTraceabilityViewer - N4 Traceability visualization for teachers
 *
 * Cortez63: Component for viewing student cognitive traceability
 *
 * Features:
 * - N4 trace timeline visualization
 * - Cognitive state distribution chart
 * - AI involvement metrics
 * - Cognitive path transitions
 * - Insights and alerts
 */

import { useState, useEffect, useCallback } from 'react';
import {
  teacherTraceabilityService,
  StudentTraceabilityResponse,
  StudentCognitivePathResponse,
  CognitiveState,
  TraceLevel,
} from '../../services/api';
import {
  Brain,
  Activity,
  Clock,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  GitBranch,
  Zap,
  Search,
  X,
} from 'lucide-react';

// =====================================================================
// TYPES
// =====================================================================

interface StudentTraceabilityViewerProps {
  studentId: string;
  activityId?: string;
  onClose?: () => void;
}

// =====================================================================
// HELPERS
// =====================================================================

const cognitiveStateColors: Record<CognitiveState, string> = {
  INICIO: 'bg-blue-500',
  EXPLORACION: 'bg-cyan-500',
  IMPLEMENTACION: 'bg-green-500',
  DEPURACION: 'bg-orange-500',
  CAMBIO_ESTRATEGIA: 'bg-purple-500',
  VALIDACION: 'bg-emerald-500',
  ESTANCAMIENTO: 'bg-red-500',
  REFLEXION: 'bg-indigo-500',
};

const cognitiveStateLabels: Record<CognitiveState, string> = {
  INICIO: 'Inicio',
  EXPLORACION: 'Exploración',
  IMPLEMENTACION: 'Implementación',
  DEPURACION: 'Depuración',
  CAMBIO_ESTRATEGIA: 'Cambio de Estrategia',
  VALIDACION: 'Validación',
  ESTANCAMIENTO: 'Estancamiento',
  REFLEXION: 'Reflexión',
};

const traceLevelColors: Record<TraceLevel, string> = {
  N1: 'bg-gray-400',
  N2: 'bg-blue-400',
  N3: 'bg-purple-400',
  N4: 'bg-emerald-400',
};

const traceLevelLabels: Record<TraceLevel, string> = {
  N1: 'N1 - Raw',
  N2: 'N2 - Preprocesado',
  N3: 'N3 - LLM',
  N4: 'N4 - Síntesis',
};

const getAIDependencyColor = (value: number): string => {
  if (value >= 0.7) return 'text-red-500';
  if (value >= 0.4) return 'text-yellow-500';
  return 'text-green-500';
};

const getAIDependencyLabel = (value: number): string => {
  if (value >= 0.7) return 'Alta';
  if (value >= 0.4) return 'Media';
  return 'Baja';
};

// =====================================================================
// COMPONENT
// =====================================================================

export function StudentTraceabilityViewer({
  studentId,
  activityId,
  onClose,
}: StudentTraceabilityViewerProps) {
  const [traceability, setTraceability] = useState<StudentTraceabilityResponse | null>(null);
  const [cognitivePath, setCognitivePath] = useState<StudentCognitivePathResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'traces' | 'path'>('overview');
  const [expandedTraces, setExpandedTraces] = useState<Set<string>>(new Set());

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [traceabilityData, pathData] = await Promise.all([
        teacherTraceabilityService.getStudentTraceability(studentId, {
          activity_id: activityId,
          limit: 100,
        }),
        teacherTraceabilityService.getStudentCognitivePath(studentId),
      ]);

      setTraceability(traceabilityData);
      setCognitivePath(pathData);
    } catch (err) {
      console.error('Error loading traceability:', err);
      setError('Error al cargar datos de trazabilidad');
    } finally {
      setIsLoading(false);
    }
  }, [studentId, activityId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const toggleTraceExpanded = (traceId: string) => {
    setExpandedTraces((prev) => {
      const next = new Set(prev);
      if (next.has(traceId)) {
        next.delete(traceId);
      } else {
        next.add(traceId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-red-500" />
        <p className="text-[var(--text-primary)] mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90"
        >
          Reintentar
        </button>
      </div>
    );
  }

  if (!traceability) {
    return (
      <div className="p-6 text-center">
        <Search className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)]" />
        <p className="text-[var(--text-secondary)]">No hay datos de trazabilidad</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center">
            <GitBranch className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-[var(--text-primary)]">
              Trazabilidad N4 - {studentId}
            </h2>
            <p className="text-sm text-[var(--text-secondary)]">
              {traceability.total_traces} trazas registradas
              {activityId && ` en ${activityId}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)]"
            title="Actualizar"
          >
            <RefreshCw className="w-4 h-4 text-[var(--text-secondary)]" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] hover:bg-[var(--bg-hover)]"
            >
              <X className="w-4 h-4 text-[var(--text-secondary)]" />
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[var(--border-color)]">
        {[
          { id: 'overview' as const, label: 'Resumen', icon: Activity },
          { id: 'traces' as const, label: 'Trazas', icon: GitBranch },
          { id: 'path' as const, label: 'Camino Cognitivo', icon: TrendingUp },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-[var(--accent-primary)] text-[var(--accent-primary)]'
                : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[var(--bg-secondary)] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <GitBranch className="w-4 h-4 text-purple-500" />
                <span className="text-sm text-[var(--text-muted)]">Total Trazas</span>
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">
                {traceability.total_traces}
              </div>
            </div>

            <div className="bg-[var(--bg-secondary)] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Zap className="w-4 h-4 text-emerald-500" />
                <span className="text-sm text-[var(--text-muted)]">Trazas N4</span>
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">
                {traceability.summary.total_n4_traces}
              </div>
            </div>

            <div className="bg-[var(--bg-secondary)] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-4 h-4 text-blue-500" />
                <span className="text-sm text-[var(--text-muted)]">Dependencia IA</span>
              </div>
              <div className={`text-2xl font-bold ${getAIDependencyColor(traceability.summary.average_ai_involvement)}`}>
                {Math.round(traceability.summary.average_ai_involvement * 100)}%
              </div>
              <div className="text-xs text-[var(--text-muted)]">
                {getAIDependencyLabel(traceability.summary.average_ai_involvement)}
              </div>
            </div>

            <div className="bg-[var(--bg-secondary)] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-orange-500" />
                <span className="text-sm text-[var(--text-muted)]">Estados Únicos</span>
              </div>
              <div className="text-2xl font-bold text-[var(--text-primary)]">
                {Object.keys(traceability.summary.cognitive_states_distribution).length}
              </div>
            </div>
          </div>

          {/* Cognitive States Distribution */}
          <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Distribución de Estados Cognitivos
            </h3>
            <div className="space-y-3">
              {Object.entries(traceability.summary.cognitive_states_distribution)
                .sort((a, b) => b[1] - a[1])
                .map(([state, count]) => {
                  // FIX CRIT-001 Cortez77: Guardia contra división por cero
                  const values = Object.values(traceability.summary.cognitive_states_distribution);
                  const maxCount = values.length > 0 ? Math.max(...values, 1) : 1;
                  const percentage = (count / maxCount) * 100;
                  const cogState = state as CognitiveState;

                  return (
                    <div key={state}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-[var(--text-primary)]">
                          {cognitiveStateLabels[cogState] || state}
                        </span>
                        <span className="text-sm text-[var(--text-muted)]">{count}</span>
                      </div>
                      <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                        <div
                          className={`h-full ${cognitiveStateColors[cogState] || 'bg-gray-500'} rounded-full transition-all`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Trace Levels Distribution */}
          <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-indigo-500" />
              Niveles de Trazabilidad
            </h3>
            <div className="flex flex-wrap gap-3">
              {Object.entries(traceability.summary.trace_levels_distribution).map(([level, count]) => {
                const traceLevel = level as TraceLevel;
                return (
                  <div
                    key={level}
                    className="flex items-center gap-2 px-3 py-2 bg-[var(--bg-secondary)] rounded-lg"
                  >
                    <div className={`w-3 h-3 rounded-full ${traceLevelColors[traceLevel] || 'bg-gray-400'}`} />
                    <span className="text-sm text-[var(--text-primary)]">
                      {traceLevelLabels[traceLevel] || level}
                    </span>
                    <span className="text-sm font-medium text-[var(--text-muted)]">({count})</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Insights from Cognitive Path */}
          {cognitivePath && cognitivePath.insights.length > 0 && (
            <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                Insights del Camino Cognitivo
              </h3>
              <div className="space-y-2">
                {cognitivePath.insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-2 p-3 rounded-lg ${
                      insight.includes('Alerta') ? 'bg-red-500/10 border border-red-500/20' : 'bg-[var(--bg-secondary)]'
                    }`}
                  >
                    {insight.includes('Alerta') ? (
                      <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                    ) : (
                      <Lightbulb className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    )}
                    <span className="text-sm text-[var(--text-primary)]">{insight}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Traces Tab */}
      {activeTab === 'traces' && (
        <div className="space-y-4">
          <div className="text-sm text-[var(--text-muted)]">
            Mostrando {traceability.returned_traces} de {traceability.total_traces} trazas
          </div>

          <div className="space-y-2">
            {traceability.traces.map((trace) => {
              const isExpanded = expandedTraces.has(trace.id);

              return (
                <div
                  key={trace.id}
                  className="bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)] overflow-hidden"
                >
                  <button
                    onClick={() => toggleTraceExpanded(trace.id)}
                    className="w-full p-4 flex items-center justify-between hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      {trace.trace_level && (
                        <div
                          className={`w-8 h-8 rounded-lg ${traceLevelColors[trace.trace_level]} flex items-center justify-center text-white text-xs font-bold`}
                        >
                          {trace.trace_level}
                        </div>
                      )}
                      <div className="text-left">
                        <div className="flex items-center gap-2">
                          {trace.cognitive_state && (
                            <span
                              className={`px-2 py-0.5 text-xs rounded-full text-white ${
                                cognitiveStateColors[trace.cognitive_state]
                              }`}
                            >
                              {cognitiveStateLabels[trace.cognitive_state]}
                            </span>
                          )}
                          {trace.ai_involvement !== null && (
                            <span
                              className={`text-xs ${getAIDependencyColor(trace.ai_involvement)}`}
                            >
                              IA: {Math.round(trace.ai_involvement * 100)}%
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-[var(--text-muted)] mt-1">
                          {trace.created_at
                            ? new Date(trace.created_at).toLocaleString()
                            : 'Sin fecha'}
                        </div>
                      </div>
                    </div>
                    {isExpanded ? (
                      <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                    )}
                  </button>

                  {isExpanded && (
                    <div className="p-4 pt-0 border-t border-[var(--border-color)]">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        {trace.interaction_type && (
                          <div>
                            <span className="text-[var(--text-muted)]">Tipo: </span>
                            <span className="text-[var(--text-primary)]">{trace.interaction_type}</span>
                          </div>
                        )}
                        {trace.strategy_type && (
                          <div>
                            <span className="text-[var(--text-muted)]">Estrategia: </span>
                            <span className="text-[var(--text-primary)]">{trace.strategy_type}</span>
                          </div>
                        )}
                        {trace.cognitive_intent && (
                          <div className="col-span-2">
                            <span className="text-[var(--text-muted)]">Intención: </span>
                            <span className="text-[var(--text-primary)]">{trace.cognitive_intent}</span>
                          </div>
                        )}
                        {trace.decision_justification && (
                          <div className="col-span-2">
                            <span className="text-[var(--text-muted)]">Justificación: </span>
                            <span className="text-[var(--text-primary)]">{trace.decision_justification}</span>
                          </div>
                        )}
                        {trace.content && (
                          <div className="col-span-2">
                            <span className="text-[var(--text-muted)]">Contenido: </span>
                            <span className="text-[var(--text-primary)] break-words">{trace.content}</span>
                          </div>
                        )}
                        {trace.agent_id && (
                          <div>
                            <span className="text-[var(--text-muted)]">Agente: </span>
                            <span className="text-[var(--text-primary)]">{trace.agent_id}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {traceability.pagination.has_more && (
            <div className="text-center py-4">
              <span className="text-sm text-[var(--text-muted)]">
                Hay más trazas disponibles...
              </span>
            </div>
          )}
        </div>
      )}

      {/* Cognitive Path Tab */}
      {activeTab === 'path' && cognitivePath && (
        <div className="space-y-6">
          {/* Time in States */}
          {Object.keys(cognitivePath.time_in_states).length > 0 && (
            <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-500" />
                Tiempo en cada Estado
              </h3>
              <div className="space-y-3">
                {Object.entries(cognitivePath.time_in_states)
                  .sort((a, b) => b[1] - a[1])
                  .map(([state, minutes]) => {
                    // FIX CRIT-001 Cortez77: Guardia contra división por cero
                    const timeValues = Object.values(cognitivePath.time_in_states);
                    const maxMinutes = timeValues.length > 0 ? Math.max(...timeValues, 1) : 1;
                    const percentage = (minutes / maxMinutes) * 100;
                    const cogState = state as CognitiveState;

                    return (
                      <div key={state}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-[var(--text-primary)]">
                            {cognitiveStateLabels[cogState] || state}
                          </span>
                          <span className="text-sm text-[var(--text-muted)]">{minutes.toFixed(1)} min</span>
                        </div>
                        <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                          <div
                            className={`h-full ${cognitiveStateColors[cogState] || 'bg-gray-500'} rounded-full transition-all`}
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          )}

          {/* Transitions */}
          {cognitivePath.transitions.length > 0 && (
            <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                Últimas Transiciones
              </h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {cognitivePath.transitions.slice(-15).reverse().map((transition, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-2 p-2 bg-[var(--bg-secondary)] rounded-lg"
                  >
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full text-white ${
                        cognitiveStateColors[transition.from]
                      }`}
                    >
                      {cognitiveStateLabels[transition.from]}
                    </span>
                    <span className="text-[var(--text-muted)]">→</span>
                    <span
                      className={`px-2 py-0.5 text-xs rounded-full text-white ${
                        cognitiveStateColors[transition.to]
                      }`}
                    >
                      {cognitiveStateLabels[transition.to]}
                    </span>
                    {transition.timestamp && (
                      <span className="ml-auto text-xs text-[var(--text-muted)]">
                        {new Date(transition.timestamp).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cognitive Path Timeline */}
          {cognitivePath.cognitive_path.length > 0 && (
            <div className="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                <GitBranch className="w-5 h-5 text-purple-500" />
                Timeline del Camino Cognitivo
              </h3>
              <div className="relative">
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-[var(--border-color)]" />
                <div className="space-y-4 max-h-80 overflow-y-auto">
                  {cognitivePath.cognitive_path.slice(-20).reverse().map((point, idx) => (
                    <div key={idx} className="relative pl-10">
                      <div
                        className={`absolute left-2 w-4 h-4 rounded-full ${
                          cognitiveStateColors[point.state]
                        }`}
                      />
                      <div className="bg-[var(--bg-secondary)] rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-[var(--text-primary)]">
                            {cognitiveStateLabels[point.state]}
                          </span>
                          {point.ai_involvement !== null && (
                            <span
                              className={`text-xs ${getAIDependencyColor(point.ai_involvement)}`}
                            >
                              IA: {Math.round(point.ai_involvement * 100)}%
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-muted)]">
                          {point.trace_level && (
                            <span className={`px-1.5 py-0.5 rounded ${traceLevelColors[point.trace_level]} text-white`}>
                              {point.trace_level}
                            </span>
                          )}
                          {point.timestamp && (
                            <span>{new Date(point.timestamp).toLocaleString()}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {cognitivePath.cognitive_path.length === 0 && (
            <div className="text-center py-12">
              <TrendingUp className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)] opacity-50" />
              <p className="text-[var(--text-secondary)]">
                No hay datos de camino cognitivo disponibles
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default StudentTraceabilityViewer;
