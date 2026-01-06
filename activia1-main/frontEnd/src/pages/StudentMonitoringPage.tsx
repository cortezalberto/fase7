/**
 * StudentMonitoringPage - Monitoreo de estudiantes en tiempo real
 *
 * HU-DOC-002: Monitoreo en Tiempo Real
 * HU-DOC-003: Comparacion de Estudiantes
 * HU-DOC-004: Alertas en Tiempo Real
 *
 * Cortez60: Implementacion de paginas de docente faltantes
 *
 * Backend endpoints utilizados:
 * - GET /api/v1/teacher/alerts - Alertas de estudiantes
 * - GET /api/v1/teacher/students/compare - Comparacion de estudiantes
 * - GET /api/v1/sessions - Sesiones activas
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { sessionsService, teacherTraceabilityService, TraceabilitySummaryResponse } from '../services/api';
import apiClient from '../services/api/client';
import { unwrapResponse } from '../utils';
import {
  Activity,
  AlertTriangle,
  Clock,
  Brain,
  Target,
  RefreshCw,
  Search,
  XCircle,
  CheckCircle,
  Zap,
  BarChart3,
  ChevronRight,
  GitBranch,
  Eye,
} from 'lucide-react';
import StudentTraceabilityViewer from '../components/teacher/StudentTraceabilityViewer';

// FIX MED-009 Cortez77: Campos opcionales para evitar errores si el backend no los envía
interface TeacherAlert {
  alert_id: string;
  student_id: string;
  session_id: string;
  activity_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  reasons: string[];
  suggestions?: string[]; // Opcional - puede no venir del backend
  metrics: {
    critical_risks: number;
    high_risks: number;
    medium_risks: number;
    ai_dependency: number;
    duration_hours: number;
    total_interactions: number;
  };
  timestamp: string;
}

interface AlertsResponse {
  total_alerts: number;
  by_severity: {
    critical: number;
    high: number;
    medium: number;
  };
  alerts: TeacherAlert[];
}

interface StudentComparison {
  activity_id: string;
  students_count: number;
  completed_count: number;
  in_progress_count: number;
  aggregate_statistics: {
    average_duration_minutes: number;
    average_interactions: number;
    average_ai_dependency: number;
    top_risks: { type: string; count: number }[];
    cognitive_states_distribution: Record<string, number>;
  };
  students: StudentData[];
}

interface StudentData {
  student_id: string;
  session_id: string;
  start_time: string;
  end_time: string | null;
  duration_minutes: number;
  total_interactions: number;
  blocked_interactions: number;
  cognitive_states_visited: string[];
  ai_dependency_average: number;
  risks_total: number;
  risks_by_type: Record<string, number>;
  status: string;
}

// Session type for active sessions display
interface SessionDisplay {
  id: string;
  student_id: string;
  activity_id: string;
  mode: string;
  status: string;
  created_at: string;
  trace_count: number;
}

type ViewMode = 'alerts' | 'comparison' | 'sessions' | 'traceability';

export default function StudentMonitoringPage() {
  const [searchParams] = useSearchParams();
  const [viewMode, setViewMode] = useState<ViewMode>('alerts');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [comparison, setComparison] = useState<StudentComparison | null>(null);
  const [sessions, setSessions] = useState<SessionDisplay[]>([]);
  const [traceabilitySummary, setTraceabilitySummary] = useState<TraceabilitySummaryResponse | null>(null);
  const [selectedStudentForTraceability, setSelectedStudentForTraceability] = useState<string | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [activityFilter, setActivityFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>(searchParams.get('student') || '');

  // Auto-refresh interval
  const [autoRefresh, setAutoRefresh] = useState(true);

  // FIX Cortez71: Removed console.error, only log in DEV
  // FIX CRIT-002 Cortez77: Agregar signal opcional para verificar abort antes de setState
  // Load alerts
  const loadAlerts = useCallback(async (signal?: AbortSignal) => {
    try {
      const params = severityFilter !== 'all' ? `?severity=${severityFilter}` : '';
      const response = await apiClient.get<{ data: AlertsResponse }>(`/teacher/alerts${params}`);
      if (signal?.aborted) return;
      // Cortez93: Use unwrapResponse utility to eliminate as unknown assertion
      setAlerts(unwrapResponse<AlertsResponse>(response.data));
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      // FIX HIGH-006 Cortez77: Logging condicional en DEV
      if (import.meta.env.DEV) console.error('Error loading alerts:', err);
    }
  }, [severityFilter]);

  // FIX CRIT-002 Cortez77: Agregar signal para verificar abort
  // Load comparison
  const loadComparison = useCallback(async (signal?: AbortSignal) => {
    if (!activityFilter) return;
    try {
      const response = await apiClient.get<{ data: StudentComparison }>(`/teacher/students/compare?activity_id=${activityFilter}`);
      if (signal?.aborted) return;
      // Cortez93: Use unwrapResponse utility to eliminate as unknown assertion
      setComparison(unwrapResponse<StudentComparison>(response.data));
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      // FIX HIGH-006 Cortez77: Logging condicional en DEV
      if (import.meta.env.DEV) console.error('Error loading comparison:', err);
    }
  }, [activityFilter]);

  // FIX CRIT-002 Cortez77: Agregar signal para verificar abort
  // Load active sessions
  const loadSessions = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await sessionsService.list('');
      if (signal?.aborted) return;
      // Filter for active sessions only
      const activeSessions = (response.data || []).filter(s => s.status === 'active');
      setSessions(activeSessions);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      // FIX HIGH-006 Cortez77: Logging condicional en DEV
      if (import.meta.env.DEV) console.error('Error loading sessions:', err);
    }
  }, []);

  // FIX CRIT-002 Cortez77: Agregar signal para verificar abort
  // Load traceability summary
  const loadTraceabilitySummary = useCallback(async (signal?: AbortSignal) => {
    try {
      const data = await teacherTraceabilityService.getTraceabilitySummary({
        activity_id: activityFilter || undefined,
      });
      if (signal?.aborted) return;
      setTraceabilitySummary(data);
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return;
      // FIX HIGH-006 Cortez77: Logging condicional en DEV
      if (import.meta.env.DEV) console.error('Error loading traceability:', err);
    }
  }, [activityFilter]);

  // FIX Cortez71 HIGH-003: Use AbortController for proper cleanup
  // FIX CRIT-002 Cortez77: Pasar signal a los callbacks para evitar memory leaks
  // Initial load and auto-refresh
  useEffect(() => {
    const abortController = new AbortController();
    const { signal } = abortController;

    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        await Promise.all([
          loadAlerts(signal),
          loadSessions(signal),
          loadTraceabilitySummary(signal)
        ]);
      } catch {
        if (!signal.aborted) setError('Error al cargar datos de monitoreo');
      } finally {
        if (!signal.aborted) setIsLoading(false);
      }
    };
    loadData();

    // Auto-refresh every 30 seconds if enabled
    let interval: ReturnType<typeof setInterval> | undefined;
    if (autoRefresh) {
      interval = setInterval(() => {
        if (!signal.aborted) {
          loadAlerts(signal);
          loadSessions(signal);
          loadTraceabilitySummary(signal);
        }
      }, 30000);
    }

    return () => {
      abortController.abort();
      if (interval) clearInterval(interval);
    };
  }, [loadAlerts, loadSessions, loadTraceabilitySummary, autoRefresh]);

  // FIX CRIT-002 Cortez77: AbortController para useEffect de comparación
  // Load comparison when activity filter changes
  useEffect(() => {
    if (activityFilter && viewMode === 'comparison') {
      const abortController = new AbortController();
      loadComparison(abortController.signal);
      return () => abortController.abort();
    }
  }, [activityFilter, viewMode, loadComparison]);

  // FIX CRIT-002 Cortez77: AbortController para useEffect de trazabilidad
  // Load traceability when viewing traceability tab
  useEffect(() => {
    if (viewMode === 'traceability') {
      const abortController = new AbortController();
      loadTraceabilitySummary(abortController.signal);
      return () => abortController.abort();
    }
  }, [viewMode, loadTraceabilitySummary]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await apiClient.post(`/teacher/alerts/${alertId}/acknowledge`);
      await loadAlerts();
    } catch {
      setError('Error al reconocer alerta');
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      default: return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  const getAIDependencyColor = (value: number) => {
    if (value >= 0.8) return 'text-red-500';
    if (value >= 0.6) return 'text-orange-500';
    if (value >= 0.4) return 'text-yellow-500';
    return 'text-green-500';
  };

  // FIX Cortez60: Memoize filtered lists to avoid recalculation on each render
  // FIX Cortez71 MED-003: Dependencies are correct - alerts/sessions are new arrays on each fetch
  const filteredAlerts = useMemo(() => {
    if (!alerts?.alerts) return [];
    return alerts.alerts.filter(alert => {
      if (searchQuery && !alert.student_id.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [alerts, searchQuery]);

  const filteredSessions = useMemo(() => {
    if (!sessions.length) return [];
    return sessions.filter(session => {
      if (searchQuery && !session.student_id?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [sessions, searchQuery]);

  // FIX MED-001 Cortez77: Memoizar views array para evitar recreacion en cada render
  const views = useMemo(() => [
    { id: 'alerts' as ViewMode, label: 'Alertas', icon: AlertTriangle, count: alerts?.total_alerts },
    { id: 'sessions' as ViewMode, label: 'Sesiones Activas', icon: Activity, count: sessions.length },
    { id: 'comparison' as ViewMode, label: 'Comparacion', icon: BarChart3 },
    { id: 'traceability' as ViewMode, label: 'Trazabilidad N4', icon: GitBranch, count: traceabilitySummary?.total_traces },
  ], [alerts?.total_alerts, sessions.length, traceabilitySummary?.total_traces]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
            Monitoreo de Estudiantes
          </h1>
          <p className="text-[var(--text-secondary)]">
            Supervisa estudiantes activos, alertas y compara rendimiento en tiempo real
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-actualizar
          </label>
          <button
            onClick={() => Promise.all([loadAlerts(), loadSessions()])}
            className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Actualizar
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400 flex items-center gap-2">
          <XCircle className="w-5 h-5" />
          {error}
          <button onClick={() => setError(null)} className="ml-auto">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
          </div>
          <h3 className="text-3xl font-bold text-[var(--text-primary)]">{sessions.length}</h3>
          <p className="text-sm text-[var(--text-secondary)]">Sesiones Activas</p>
        </div>

        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            {alerts?.by_severity.critical ? (
              <span className="text-xs px-2 py-1 bg-red-500/10 text-red-500 rounded-full animate-pulse">
                Criticas: {alerts.by_severity.critical}
              </span>
            ) : null}
          </div>
          <h3 className="text-3xl font-bold text-[var(--text-primary)]">{alerts?.total_alerts || 0}</h3>
          <p className="text-sm text-[var(--text-secondary)]">Alertas Activas</p>
        </div>

        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
          </div>
          <h3 className="text-3xl font-bold text-[var(--text-primary)]">{alerts?.by_severity.high || 0}</h3>
          <p className="text-sm text-[var(--text-secondary)]">Alertas Altas</p>
        </div>

        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
          </div>
          <h3 className="text-3xl font-bold text-[var(--text-primary)]">{alerts?.by_severity.medium || 0}</h3>
          <p className="text-sm text-[var(--text-secondary)]">Alertas Medias</p>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-2 border-b border-[var(--border-color)]">
        {views.map((view) => (
          <button
            key={view.id}
            onClick={() => setViewMode(view.id)}
            className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
              viewMode === view.id
                ? 'border-[var(--accent-primary)] text-[var(--accent-primary)]'
                : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
            }`}
          >
            <view.icon className="w-4 h-4" />
            {view.label}
            {view.count !== undefined && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-tertiary)]">
                {view.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Search and Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex-1 min-w-[200px]">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar estudiante..."
              className="w-full pl-10 pr-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
            />
          </div>
        </div>

        {viewMode === 'alerts' && (
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
          >
            <option value="all">Todas las severidades</option>
            <option value="critical">Critica</option>
            <option value="high">Alta</option>
            <option value="medium">Media</option>
          </select>
        )}

        {viewMode === 'comparison' && (
          <input
            type="text"
            value={activityFilter}
            onChange={(e) => setActivityFilter(e.target.value)}
            placeholder="ID de actividad..."
            className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
          />
        )}
      </div>

      {/* Content */}
      <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] overflow-hidden">
        {/* Alerts View */}
        {viewMode === 'alerts' && (
          filteredAlerts.length === 0 ? (
            <div className="text-center py-12 text-[var(--text-muted)]">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
              <p className="text-lg font-medium text-[var(--text-primary)] mb-2">Sin alertas activas</p>
              <p>Todos los estudiantes progresan sin problemas</p>
            </div>
          ) : (
            <div className="divide-y divide-[var(--border-color)]">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.alert_id}
                  className="p-4 hover:bg-[var(--bg-hover)] transition-colors"
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      alert.severity === 'critical' ? 'bg-red-500/10 text-red-500' :
                      alert.severity === 'high' ? 'bg-orange-500/10 text-orange-500' :
                      'bg-yellow-500/10 text-yellow-500'
                    }`}>
                      <AlertTriangle className="w-5 h-5" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-[var(--text-primary)]">
                          {alert.student_id}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${getSeverityColor(alert.severity)}`}>
                          {alert.severity}
                        </span>
                      </div>

                      <p className="text-sm text-[var(--text-secondary)] mb-2">
                        {alert.reasons.join(' • ')}
                      </p>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-[var(--text-muted)]">
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          {alert.activity_id}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {alert.metrics.duration_hours.toFixed(1)}h
                        </span>
                        <span className={`flex items-center gap-1 ${getAIDependencyColor(alert.metrics.ai_dependency)}`}>
                          <Brain className="w-3 h-3" />
                          IA: {Math.round(alert.metrics.ai_dependency * 100)}%
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          {alert.metrics.total_interactions} interacciones
                        </span>
                      </div>

                      {/* FIX MED-009 Cortez77: Verificar suggestions antes de acceder */}
                      {alert.suggestions && alert.suggestions.length > 0 && (
                        <div className="mt-3 p-2 bg-[var(--bg-secondary)] rounded text-xs">
                          <span className="font-medium text-[var(--text-muted)]">Sugerencias: </span>
                          <span className="text-[var(--text-secondary)]">{alert.suggestions.join(' • ')}</span>
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleAcknowledgeAlert(alert.alert_id)}
                      className="px-3 py-1 text-sm bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] rounded hover:bg-[var(--accent-primary)]/20 flex-shrink-0"
                    >
                      Atender
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Sessions View */}
        {viewMode === 'sessions' && (
          filteredSessions.length === 0 ? (
            <div className="text-center py-12 text-[var(--text-muted)]">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium text-[var(--text-primary)] mb-2">Sin sesiones activas</p>
              <p>No hay estudiantes trabajando en este momento</p>
            </div>
          ) : (
            <div className="divide-y divide-[var(--border-color)]">
              {filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className="p-4 hover:bg-[var(--bg-hover)] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center flex-shrink-0">
                      <Zap className="w-5 h-5 text-green-500" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-[var(--text-primary)]">
                          {session.student_id}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          session.mode === 'TUTOR' ? 'bg-purple-500/10 text-purple-400' :
                          session.mode === 'SIMULATOR' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-green-500/10 text-green-400'
                        }`}>
                          {session.mode}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          {session.activity_id}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Iniciado: {new Date(session.created_at).toLocaleTimeString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Target className="w-3 h-3" />
                          {session.trace_count} trazas
                        </span>
                      </div>
                    </div>

                    <ChevronRight className="w-5 h-5 text-[var(--text-muted)]" />
                  </div>
                </div>
              ))}
            </div>
          )
        )}

        {/* Comparison View */}
        {viewMode === 'comparison' && (
          !activityFilter ? (
            <div className="text-center py-12 text-[var(--text-muted)]">
              <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium text-[var(--text-primary)] mb-2">Ingresa un ID de actividad</p>
              <p>Escribe el ID de una actividad para comparar el rendimiento de estudiantes</p>
            </div>
          ) : !comparison ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-[var(--accent-primary)] border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Aggregate Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {comparison.students_count}
                  </div>
                  <div className="text-sm text-[var(--text-muted)]">Estudiantes</div>
                </div>
                <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {comparison.aggregate_statistics.average_duration_minutes.toFixed(0)} min
                  </div>
                  <div className="text-sm text-[var(--text-muted)]">Duracion Promedio</div>
                </div>
                <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                  <div className="text-2xl font-bold text-[var(--text-primary)]">
                    {comparison.aggregate_statistics.average_interactions.toFixed(0)}
                  </div>
                  <div className="text-sm text-[var(--text-muted)]">Interacciones Promedio</div>
                </div>
                <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                  <div className={`text-2xl font-bold ${getAIDependencyColor(comparison.aggregate_statistics.average_ai_dependency)}`}>
                    {Math.round(comparison.aggregate_statistics.average_ai_dependency * 100)}%
                  </div>
                  <div className="text-sm text-[var(--text-muted)]">Dependencia IA Promedio</div>
                </div>
              </div>

              {/* Students Table */}
              <div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                  Detalle por Estudiante
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-[var(--border-color)]">
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Estudiante</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Estado</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Duracion</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Interacciones</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Dep. IA</th>
                        <th className="px-4 py-3 text-left text-sm font-medium text-[var(--text-muted)]">Riesgos</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.students.map((student) => (
                        <tr key={student.session_id} className="border-b border-[var(--border-color)] hover:bg-[var(--bg-hover)]">
                          <td className="px-4 py-3 text-sm text-[var(--text-primary)]">{student.student_id}</td>
                          <td className="px-4 py-3">
                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                              student.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                              student.status === 'active' ? 'bg-blue-500/10 text-blue-500' :
                              'bg-yellow-500/10 text-yellow-500'
                            }`}>
                              {student.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                            {student.duration_minutes.toFixed(0)} min
                          </td>
                          <td className="px-4 py-3 text-sm text-[var(--text-secondary)]">
                            {student.total_interactions}
                            {student.blocked_interactions > 0 && (
                              <span className="ml-1 text-red-500">({student.blocked_interactions} bloq.)</span>
                            )}
                          </td>
                          <td className={`px-4 py-3 text-sm ${getAIDependencyColor(student.ai_dependency_average)}`}>
                            {Math.round(student.ai_dependency_average * 100)}%
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {student.risks_total > 0 ? (
                              <span className="text-red-500">{student.risks_total}</span>
                            ) : (
                              <span className="text-green-500">0</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Top Risks */}
              {comparison.aggregate_statistics.top_risks.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                    Riesgos mas Frecuentes
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {comparison.aggregate_statistics.top_risks.map((risk) => (
                      <span key={risk.type} className="px-3 py-1 bg-red-500/10 text-red-500 rounded-full text-sm">
                        {risk.type}: {risk.count}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )
        )}

        {/* Traceability View */}
        {viewMode === 'traceability' && (
          selectedStudentForTraceability ? (
            <div className="p-6">
              <StudentTraceabilityViewer
                studentId={selectedStudentForTraceability}
                activityId={activityFilter || undefined}
                onClose={() => setSelectedStudentForTraceability(null)}
              />
            </div>
          ) : (
            <div className="p-6 space-y-6">
              {/* Traceability Summary */}
              {traceabilitySummary ? (
                <>
                  {/* Stats Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                      <div className="text-2xl font-bold text-[var(--text-primary)]">
                        {traceabilitySummary.total_students}
                      </div>
                      <div className="text-sm text-[var(--text-muted)]">Estudiantes con Trazas</div>
                    </div>
                    <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                      <div className="text-2xl font-bold text-[var(--text-primary)]">
                        {traceabilitySummary.total_traces}
                      </div>
                      <div className="text-sm text-[var(--text-muted)]">Total Trazas N4</div>
                    </div>
                    <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                      <div className="text-2xl font-bold text-red-500">
                        {traceabilitySummary.ai_dependency_distribution.high}
                      </div>
                      <div className="text-sm text-[var(--text-muted)]">Alta Dependencia IA</div>
                    </div>
                    <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                      <div className="text-2xl font-bold text-green-500">
                        {traceabilitySummary.ai_dependency_distribution.low}
                      </div>
                      <div className="text-sm text-[var(--text-muted)]">Baja Dependencia IA</div>
                    </div>
                  </div>

                  {/* Cognitive States Global Distribution */}
                  {Object.keys(traceabilitySummary.cognitive_states_global).length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                        <Brain className="w-5 h-5 text-purple-500" />
                        Distribucion Global de Estados Cognitivos
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(traceabilitySummary.cognitive_states_global)
                          .sort((a, b) => b[1] - a[1])
                          .map(([state, count]) => (
                            <span
                              key={state}
                              className="px-3 py-1 bg-purple-500/10 text-purple-400 rounded-full text-sm"
                            >
                              {state}: {count}
                            </span>
                          ))}
                      </div>
                    </div>
                  )}

                  {/* Traceability Alerts */}
                  {traceabilitySummary.alerts.length > 0 && (
                    <div>
                      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-500" />
                        Alertas de Trazabilidad
                      </h3>
                      <div className="space-y-2">
                        {traceabilitySummary.alerts.map((alert, idx) => (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg ${
                              alert.severity === 'critical'
                                ? 'bg-red-500/10 border border-red-500/20'
                                : 'bg-yellow-500/10 border border-yellow-500/20'
                            }`}
                          >
                            <div className="flex items-start gap-2">
                              <AlertTriangle
                                className={`w-4 h-4 mt-0.5 ${
                                  alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'
                                }`}
                              />
                              <div>
                                <p className="text-sm text-[var(--text-primary)]">{alert.message}</p>
                                {alert.students && alert.students.length > 0 && (
                                  <div className="mt-2 flex flex-wrap gap-1">
                                    {alert.students.map((studentId) => (
                                      <button
                                        key={studentId}
                                        onClick={() => setSelectedStudentForTraceability(studentId)}
                                        className="text-xs px-2 py-1 bg-[var(--bg-secondary)] text-[var(--text-secondary)] rounded hover:text-[var(--accent-primary)] transition-colors"
                                      >
                                        {studentId}
                                      </button>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Students by AI Dependency */}
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                      Estudiantes por Dependencia de IA
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* High AI Dependency */}
                      <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-red-500 mb-3">Alta (&gt;70%)</h4>
                        {traceabilitySummary.students_by_ai_dependency.high.length > 0 ? (
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {traceabilitySummary.students_by_ai_dependency.high.map((studentId) => (
                              <button
                                key={studentId}
                                onClick={() => setSelectedStudentForTraceability(studentId)}
                                className="w-full flex items-center justify-between p-2 bg-[var(--bg-secondary)] rounded hover:bg-[var(--bg-hover)] transition-colors"
                              >
                                <span className="text-sm text-[var(--text-primary)]">{studentId}</span>
                                <Eye className="w-4 h-4 text-[var(--text-muted)]" />
                              </button>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-[var(--text-muted)]">Ninguno</p>
                        )}
                      </div>

                      {/* Medium AI Dependency */}
                      <div className="bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-yellow-500 mb-3">Media (40-70%)</h4>
                        {traceabilitySummary.students_by_ai_dependency.medium.length > 0 ? (
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {traceabilitySummary.students_by_ai_dependency.medium.map((studentId) => (
                              <button
                                key={studentId}
                                onClick={() => setSelectedStudentForTraceability(studentId)}
                                className="w-full flex items-center justify-between p-2 bg-[var(--bg-secondary)] rounded hover:bg-[var(--bg-hover)] transition-colors"
                              >
                                <span className="text-sm text-[var(--text-primary)]">{studentId}</span>
                                <Eye className="w-4 h-4 text-[var(--text-muted)]" />
                              </button>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-[var(--text-muted)]">Ninguno</p>
                        )}
                      </div>

                      {/* Low AI Dependency */}
                      <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-4">
                        <h4 className="text-sm font-medium text-green-500 mb-3">Baja (&lt;40%)</h4>
                        {traceabilitySummary.students_by_ai_dependency.low.length > 0 ? (
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {traceabilitySummary.students_by_ai_dependency.low.map((studentId) => (
                              <button
                                key={studentId}
                                onClick={() => setSelectedStudentForTraceability(studentId)}
                                className="w-full flex items-center justify-between p-2 bg-[var(--bg-secondary)] rounded hover:bg-[var(--bg-hover)] transition-colors"
                              >
                                <span className="text-sm text-[var(--text-primary)]">{studentId}</span>
                                <Eye className="w-4 h-4 text-[var(--text-muted)]" />
                              </button>
                            ))}
                          </div>
                        ) : (
                          <p className="text-xs text-[var(--text-muted)]">Ninguno</p>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-12 text-[var(--text-muted)]">
                  <GitBranch className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium text-[var(--text-primary)] mb-2">Sin datos de trazabilidad</p>
                  <p>No hay trazas cognitivas registradas</p>
                </div>
              )}
            </div>
          )
        )}
      </div>
    </div>
  );
}
