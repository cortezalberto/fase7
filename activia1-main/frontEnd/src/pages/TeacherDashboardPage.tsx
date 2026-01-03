/**
 * TeacherDashboardPage - Panel principal del docente
 *
 * HU-DOC-001: Dashboard de Supervision
 * HU-DOC-002: Monitoreo en Tiempo Real
 *
 * Cortez60: Implementacion de paginas de docente faltantes
 *
 * Backend endpoints utilizados:
 * - GET /api/v1/teacher/alerts - Alertas de estudiantes
 * - GET /api/v1/teacher/students/compare - Comparacion de estudiantes
 * - GET /api/v1/reports/analytics - Metricas de aprendizaje
 * - GET /api/v1/admin/risks/dashboard - Dashboard de riesgos
 */
import { useState, useEffect, useMemo, memo } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  reportsService,
  institutionalRisksService,
  teacherTraceabilityService,
  LearningAnalytics,
  RiskDashboard,
  TraceabilitySummaryResponse,
} from '../services/api';
import apiClient from '../services/api/client';
import {
  Users,
  AlertTriangle,
  Activity,
  // FIX Cortez71 MED-006: Removed unused BookOpen import
  FileText,
  Shield,
  ArrowRight,
  Clock,
  CheckCircle,
  Eye,
  Bell,
  GitBranch,
  Brain,
} from 'lucide-react';

interface TeacherAlert {
  alert_id: string;
  student_id: string;
  session_id: string;
  activity_id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  reasons: string[];
  suggestions: string[];
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

interface StatCard {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ElementType;
  color: string;
  link?: string;
}

export default function TeacherDashboardPage() {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [analytics, setAnalytics] = useState<LearningAnalytics | null>(null);
  // FIX Cortez71 MED-006: Prefixed with _ to indicate intentionally unused (for future risk section)
  const [_riskDashboard, setRiskDashboard] = useState<RiskDashboard | null>(null);
  const [traceabilitySummary, setTraceabilitySummary] = useState<TraceabilitySummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const fetchData = async () => {
      try {
        setError(null);

        // Fetch all data in parallel
        const [alertsRes, analyticsRes, riskRes, traceabilityRes] = await Promise.allSettled([
          apiClient.get<{ data: AlertsResponse }>('/teacher/alerts'),
          reportsService.getLearningAnalytics('month'),
          institutionalRisksService.getDashboard(),
          teacherTraceabilityService.getTraceabilitySummary(),
        ]);

        if (!abortController.signal.aborted) {
          // Handle alerts
          if (alertsRes.status === 'fulfilled') {
            const data = alertsRes.value.data;
            setAlerts('data' in data ? data.data : data as unknown as AlertsResponse);
          }

          // Handle analytics
          if (analyticsRes.status === 'fulfilled') {
            setAnalytics(analyticsRes.value);
          }

          // Handle risk dashboard
          if (riskRes.status === 'fulfilled') {
            setRiskDashboard(riskRes.value);
          }

          // Handle traceability summary (Cortez63)
          if (traceabilityRes.status === 'fulfilled') {
            setTraceabilitySummary(traceabilityRes.value);
          }
        }
      } catch (err) {
        if (!abortController.signal.aborted) {
          console.error('Error fetching teacher dashboard data:', err);
          setError('Error al cargar datos del dashboard');
        }
      } finally {
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    fetchData();
    return () => abortController.abort();
  }, []);

  // Memoize stats
  const stats: StatCard[] = useMemo(() => [
    {
      title: 'Estudiantes Activos',
      value: analytics?.total_students || 0,
      change: 'Este mes',
      changeType: 'neutral',
      icon: Users,
      color: 'from-blue-500 to-cyan-600',
      link: '/teacher/monitoring',
    },
    {
      title: 'Sesiones Totales',
      value: analytics?.total_sessions || 0,
      change: `${analytics?.avg_session_duration ? Math.round(analytics.avg_session_duration) : 0} min promedio`,
      changeType: 'neutral',
      icon: Activity,
      color: 'from-green-500 to-emerald-600',
    },
    {
      title: 'Alertas Activas',
      value: alerts?.total_alerts || 0,
      change: alerts?.by_severity.critical ? `${alerts.by_severity.critical} criticas` : 'Sin criticas',
      changeType: alerts?.by_severity.critical ? 'negative' : 'positive',
      icon: AlertTriangle,
      color: alerts?.by_severity.critical ? 'from-red-500 to-rose-600' : 'from-yellow-500 to-orange-600',
      link: '/teacher/monitoring',
    },
    {
      title: 'Trazas N4',
      value: traceabilitySummary?.total_traces || 0,
      change: traceabilitySummary?.ai_dependency_distribution.high
        ? `${traceabilitySummary.ai_dependency_distribution.high} alta dep. IA`
        : 'Sin alertas',
      changeType: traceabilitySummary?.ai_dependency_distribution.high ? 'negative' : 'positive',
      icon: GitBranch,
      color: 'from-indigo-500 to-purple-600',
      link: '/teacher/monitoring',
    },
  ], [alerts, analytics, traceabilitySummary]);

  const quickActions = [
    {
      title: 'Monitoreo en Vivo',
      description: 'Ver estudiantes activos en tiempo real',
      icon: Eye,
      path: '/teacher/monitoring',
      gradient: 'from-indigo-500 to-purple-600',
    },
    {
      title: 'Trazabilidad N4',
      description: 'Analisis cognitivo de estudiantes',
      icon: GitBranch,
      path: '/teacher/monitoring?tab=traceability',
      gradient: 'from-purple-500 to-pink-600',
    },
    {
      title: 'Generar Reportes',
      description: 'Reportes de cohorte y rendimiento',
      icon: FileText,
      path: '/teacher/reports',
      gradient: 'from-green-500 to-emerald-600',
    },
    {
      title: 'Gestion de Riesgos',
      description: 'Alertas y planes de remediacion',
      icon: Shield,
      path: '/teacher/risks',
      gradient: 'from-orange-500 to-red-600',
    },
  ];

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
            Panel del Docente
          </h1>
          <p className="text-[var(--text-secondary)]">
            Bienvenido, {user?.full_name || user?.username}. Supervisa el progreso de tus estudiantes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/teacher/monitoring"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--accent-primary)] text-white hover:opacity-90 transition-opacity"
          >
            <Bell className="w-4 h-4" />
            <span className="hidden sm:inline">Ver Alertas</span>
            {alerts?.total_alerts ? (
              <span className="bg-white/20 px-2 py-0.5 rounded-full text-xs">
                {alerts.total_alerts}
              </span>
            ) : null}
          </Link>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.title}
            className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6 hover:border-[var(--border-light)] transition-all duration-300 group"
          >
            {stat.link ? (
              <Link to={stat.link} className="block">
                <StatCardContent stat={stat} />
              </Link>
            ) : (
              <StatCardContent stat={stat} />
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
          Acciones Rapidas
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {quickActions.map((action) => (
            <Link
              key={action.path}
              to={action.path}
              className="group bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6 hover:border-[var(--accent-primary)]/50 transition-all duration-300 hover:shadow-lg hover:shadow-[var(--accent-primary)]/10"
            >
              <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <action.icon className="w-7 h-7 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2 group-hover:text-[var(--accent-primary)] transition-colors">
                {action.title}
              </h3>
              <p className="text-sm text-[var(--text-secondary)] mb-4">
                {action.description}
              </p>
              <div className="flex items-center text-[var(--accent-primary)] text-sm font-medium">
                Ir
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-2 transition-transform" />
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Alerts */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-[var(--text-primary)]">
            Alertas Recientes
          </h2>
          <Link
            to="/teacher/monitoring"
            className="text-sm text-[var(--accent-primary)] hover:text-[var(--accent-secondary)] flex items-center gap-1"
          >
            Ver todas
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {!alerts?.alerts.length ? (
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h3 className="text-lg font-medium text-[var(--text-primary)] mb-2">
              Sin alertas activas
            </h3>
            <p className="text-[var(--text-secondary)]">
              Todos los estudiantes estan progresando sin problemas
            </p>
          </div>
        ) : (
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] overflow-hidden">
            <div className="divide-y divide-[var(--border-color)]">
              {alerts.alerts.slice(0, 5).map((alert) => (
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
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          alert.severity === 'critical' ? 'bg-red-500/10 text-red-500' :
                          alert.severity === 'high' ? 'bg-orange-500/10 text-orange-500' :
                          'bg-yellow-500/10 text-yellow-500'
                        }`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-[var(--text-secondary)] line-clamp-1">
                        {alert.reasons.join(', ')}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-[var(--text-muted)]">
                        <span className="flex items-center gap-1">
                          <Activity className="w-3 h-3" />
                          {alert.activity_id}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {alert.metrics.duration_hours.toFixed(1)}h
                        </span>
                      </div>
                    </div>
                    <Link
                      to={`/teacher/monitoring?student=${alert.student_id}`}
                      className="text-[var(--accent-primary)] hover:text-[var(--accent-secondary)] p-2"
                    >
                      <Eye className="w-5 h-5" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Agent Usage Chart */}
      {analytics?.most_used_agents && analytics.most_used_agents.length > 0 && (
        <div>
          <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
            Uso de Agentes IA
          </h2>
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
            <div className="space-y-4">
              {analytics.most_used_agents.map((agent) => (
                <div key={agent.agent}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-[var(--text-primary)]">
                      {agent.agent}
                    </span>
                    <span className="text-sm text-[var(--text-muted)]">
                      {agent.usage_count} usos
                    </span>
                  </div>
                  <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"
                      style={{
                        width: `${Math.min((agent.usage_count / Math.max(...analytics.most_used_agents.map(a => a.usage_count))) * 100, 100)}%`
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Traceability Summary (Cortez63) */}
      {traceabilitySummary && Object.keys(traceabilitySummary.cognitive_states_global).length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Brain className="w-5 h-5 text-purple-500" />
              Trazabilidad Cognitiva N4
            </h2>
            <Link
              to="/teacher/monitoring"
              className="text-sm text-[var(--accent-primary)] hover:text-[var(--accent-secondary)] flex items-center gap-1"
            >
              Ver detalle
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Cognitive States Distribution */}
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <h3 className="text-sm font-medium text-[var(--text-muted)] mb-4">
                Estados Cognitivos Detectados
              </h3>
              <div className="space-y-3">
                {Object.entries(traceabilitySummary.cognitive_states_global)
                  .sort((a, b) => b[1] - a[1])
                  .slice(0, 5)
                  .map(([state, count]) => {
                    const maxCount = Math.max(...Object.values(traceabilitySummary.cognitive_states_global));
                    const percentage = (count / maxCount) * 100;

                    return (
                      <div key={state}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm text-[var(--text-primary)]">{state}</span>
                          <span className="text-xs text-[var(--text-muted)]">{count}</span>
                        </div>
                        <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-purple-500 to-indigo-600 rounded-full"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>

            {/* AI Dependency Distribution */}
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <h3 className="text-sm font-medium text-[var(--text-muted)] mb-4">
                Dependencia de IA por Estudiantes
              </h3>
              <div className="flex items-center justify-center gap-8 py-4">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mb-2 mx-auto">
                    <span className="text-2xl font-bold text-red-500">
                      {traceabilitySummary.ai_dependency_distribution.high}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-muted)]">Alta (&gt;70%)</span>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-yellow-500/10 flex items-center justify-center mb-2 mx-auto">
                    <span className="text-2xl font-bold text-yellow-500">
                      {traceabilitySummary.ai_dependency_distribution.medium}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-muted)]">Media (40-70%)</span>
                </div>
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-green-500/10 flex items-center justify-center mb-2 mx-auto">
                    <span className="text-2xl font-bold text-green-500">
                      {traceabilitySummary.ai_dependency_distribution.low}
                    </span>
                  </div>
                  <span className="text-xs text-[var(--text-muted)]">Baja (&lt;40%)</span>
                </div>
              </div>

              {/* FIX Cortez71 HIGH-005: Use stable key based on message content */}
              {/* Traceability Alerts */}
              {traceabilitySummary.alerts.length > 0 && (
                <div className="mt-4 pt-4 border-t border-[var(--border-color)]">
                  <div className="space-y-2">
                    {traceabilitySummary.alerts.slice(0, 2).map((alert) => (
                      <div
                        key={`alert-${alert.type}-${alert.message.slice(0, 30)}`}
                        className={`flex items-start gap-2 p-2 rounded-lg text-xs ${
                          alert.severity === 'critical'
                            ? 'bg-red-500/10 text-red-400'
                            : 'bg-yellow-500/10 text-yellow-400'
                        }`}
                      >
                        <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        <span>{alert.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// FIX Cortez71 LOW-012: Memoized pure presentational component
const StatCardContent = memo(function StatCardContent({ stat }: { stat: StatCard }) {
  return (
    <>
      <div className="flex items-start justify-between mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
          <stat.icon className="w-6 h-6 text-white" aria-hidden="true" />
        </div>
        {stat.change && (
          <span className={`text-xs px-2 py-1 rounded-full ${
            stat.changeType === 'positive' ? 'bg-green-500/10 text-green-500' :
            stat.changeType === 'negative' ? 'bg-red-500/10 text-red-500' :
            'bg-[var(--bg-tertiary)] text-[var(--text-muted)]'
          }`}>
            {stat.change}
          </span>
        )}
      </div>
      <h3 className="text-3xl font-bold text-[var(--text-primary)] mb-1">
        {stat.value}
      </h3>
      <p className="text-sm text-[var(--text-secondary)]">{stat.title}</p>
    </>
  );
});
