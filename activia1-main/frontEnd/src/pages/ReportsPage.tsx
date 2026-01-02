/**
 * ReportsPage - Generacion de reportes para docentes
 *
 * HU-DOC-003: Reportes de Cohorte
 * HU-DOC-004: Reportes Individuales
 * HU-DOC-009: Comparativa entre Cohortes
 *
 * Cortez60: Implementacion de paginas de docente faltantes
 *
 * Backend endpoints utilizados:
 * - POST /api/v1/reports/cohort - Generar reporte de cohorte
 * - POST /api/v1/reports/risk-dashboard - Dashboard de riesgos
 * - GET /api/v1/reports/teacher/{teacher_id} - Reportes del docente
 * - GET /api/v1/reports/analytics - Analiticas de aprendizaje
 * - GET /api/v1/export/history - Historial de exportaciones
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
  reportsService,
  CohortReport,
  CohortReportRequest,
  RiskDashboardReport,
  RiskDashboardRequest,
  LearningAnalytics,
  ExportHistoryItem,
} from '../services/api';
import {
  FileText,
  Download,
  Users,
  AlertTriangle,
  BarChart3,
  XCircle,
  RefreshCw,
} from 'lucide-react';

type ReportType = 'cohort' | 'risk' | 'analytics';

export default function ReportsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<ReportType>('cohort');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Report data
  const [cohortReport, setCohortReport] = useState<CohortReport | null>(null);
  const [riskReport, setRiskReport] = useState<RiskDashboardReport | null>(null);
  const [analytics, setAnalytics] = useState<LearningAnalytics | null>(null);
  const [exportHistory, setExportHistory] = useState<ExportHistoryItem[]>([]);

  // Form state
  const [courseId, setCourseId] = useState('');
  const [studentIds, setStudentIds] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [exportFormat, setExportFormat] = useState<'json' | 'pdf' | 'xlsx'>('pdf');

  // Load export history on mount
  useEffect(() => {
    let isMounted = true;
    const loadExportHistory = async () => {
      try {
        const history = await reportsService.getExportHistory();
        if (isMounted) setExportHistory(history);
      } catch (err) {
        if (isMounted) console.error('Error loading export history:', err);
      }
    };
    loadExportHistory();
    return () => { isMounted = false; };
  }, []);

  // Load analytics on mount
  useEffect(() => {
    let isMounted = true;
    const loadAnalytics = async () => {
      try {
        const data = await reportsService.getLearningAnalytics('month');
        if (isMounted) setAnalytics(data);
      } catch (err) {
        if (isMounted) console.error('Error loading analytics:', err);
      }
    };
    loadAnalytics();
    return () => { isMounted = false; };
  }, []);

  const handleGenerateCohortReport = async () => {
    if (!courseId || !periodStart || !periodEnd) {
      setError('Por favor complete todos los campos requeridos');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: CohortReportRequest = {
        course_id: courseId,
        teacher_id: user?.id || '',
        student_ids: studentIds ? studentIds.split(',').map(s => s.trim()) : [],
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
        export_format: exportFormat,
      };

      const report = await reportsService.generateCohortReport(request);
      setCohortReport(report);
    } catch (err) {
      setError('Error al generar el reporte de cohorte');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateRiskReport = async () => {
    if (!courseId || !periodStart || !periodEnd) {
      setError('Por favor complete todos los campos requeridos');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const request: RiskDashboardRequest = {
        course_id: courseId,
        teacher_id: user?.id || '',
        student_ids: studentIds ? studentIds.split(',').map(s => s.trim()) : [],
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
      };

      const report = await reportsService.generateRiskDashboard(request);
      setRiskReport(report);
    } catch (err) {
      setError('Error al generar el dashboard de riesgos');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadReport = async (reportId: string) => {
    try {
      const blob = await reportsService.downloadReport(reportId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${reportId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError('Error al descargar el reporte');
      console.error(err);
    }
  };

  const tabs = [
    { id: 'cohort' as ReportType, label: 'Reporte de Cohorte', icon: Users },
    { id: 'risk' as ReportType, label: 'Dashboard de Riesgos', icon: AlertTriangle },
    { id: 'analytics' as ReportType, label: 'Analiticas', icon: BarChart3 },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
          Reportes y Analiticas
        </h1>
        <p className="text-[var(--text-secondary)]">
          Genera reportes de cohorte, analiza riesgos y visualiza tendencias de aprendizaje
        </p>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-red-400 flex items-center gap-2">
          <XCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-[var(--border-color)]">
        {tabs.map((tab) => (
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

      {/* Tab Content */}
      <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
        {activeTab === 'cohort' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Generar Reporte de Cohorte
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  ID del Curso *
                </label>
                <input
                  type="text"
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value)}
                  placeholder="ej: prog2_2024_1"
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  IDs de Estudiantes (opcional, separados por coma)
                </label>
                <input
                  type="text"
                  value={studentIds}
                  onChange={(e) => setStudentIds(e.target.value)}
                  placeholder="ej: student_001, student_002"
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Fecha Inicio *
                </label>
                <input
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Fecha Fin *
                </label>
                <input
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Formato de Exportacion
                </label>
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value as 'json' | 'pdf' | 'xlsx')}
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                >
                  <option value="pdf">PDF</option>
                  <option value="xlsx">Excel (XLSX)</option>
                  <option value="json">JSON</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleGenerateCohortReport}
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-3 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {isLoading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <FileText className="w-5 h-5" />
              )}
              Generar Reporte
            </button>

            {/* Cohort Report Results */}
            {cohortReport && (
              <div className="mt-8 space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                    Resultados del Reporte
                  </h3>
                  <button
                    onClick={() => handleDownloadReport(cohortReport.report_id)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-500 rounded-lg hover:bg-green-500/20 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Descargar
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {cohortReport.summary.total_students}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Estudiantes</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {cohortReport.summary.total_sessions}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Sesiones</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {Math.round(cohortReport.summary.completion_rate * 100)}%
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Tasa de Completado</div>
                  </div>
                </div>

                {/* Risk Summary */}
                {cohortReport.risk_summary && (
                  <div>
                    <h4 className="text-md font-medium text-[var(--text-primary)] mb-3">
                      Resumen de Riesgos
                    </h4>
                    <div className="flex gap-4">
                      <span className="px-3 py-1 bg-red-500/10 text-red-500 rounded-full text-sm">
                        Criticos: {cohortReport.risk_summary.critical_count}
                      </span>
                      <span className="px-3 py-1 bg-orange-500/10 text-orange-500 rounded-full text-sm">
                        Altos: {cohortReport.risk_summary.high_count}
                      </span>
                      <span className="px-3 py-1 bg-yellow-500/10 text-yellow-500 rounded-full text-sm">
                        Medios: {cohortReport.risk_summary.medium_count}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'risk' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Dashboard de Riesgos
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  ID del Curso *
                </label>
                <input
                  type="text"
                  value={courseId}
                  onChange={(e) => setCourseId(e.target.value)}
                  placeholder="ej: prog2_2024_1"
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  IDs de Estudiantes (opcional)
                </label>
                <input
                  type="text"
                  value={studentIds}
                  onChange={(e) => setStudentIds(e.target.value)}
                  placeholder="Separados por coma"
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Fecha Inicio *
                </label>
                <input
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
                  Fecha Fin *
                </label>
                <input
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                  className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                />
              </div>
            </div>

            <button
              onClick={handleGenerateRiskReport}
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-3 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              {isLoading ? (
                <RefreshCw className="w-5 h-5 animate-spin" />
              ) : (
                <AlertTriangle className="w-5 h-5" />
              )}
              Generar Dashboard
            </button>

            {/* Risk Report Results */}
            {riskReport && (
              <div className="mt-8 space-y-6">
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  Resultados del Analisis de Riesgos
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {riskReport.summary.total_risks}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Total Riesgos</div>
                  </div>
                  <div className="bg-red-500/10 rounded-lg p-4">
                    <div className="text-2xl font-bold text-red-500">
                      {Math.round(riskReport.summary.critical_percentage)}%
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Criticos</div>
                  </div>
                  <div className="bg-green-500/10 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-500">
                      {Math.round(riskReport.summary.resolution_rate * 100)}%
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Tasa Resolucion</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {riskReport.summary.avg_time_to_resolve_hours.toFixed(1)}h
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Tiempo Promedio</div>
                  </div>
                </div>

                {/* Top Affected Students */}
                {riskReport.top_affected_students.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-[var(--text-primary)] mb-3">
                      Estudiantes Mas Afectados
                    </h4>
                    <div className="space-y-2">
                      {riskReport.top_affected_students.map((student) => (
                        <div
                          key={student.student_id}
                          className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-lg"
                        >
                          <span className="text-[var(--text-primary)]">{student.student_id}</span>
                          <span className="px-2 py-1 bg-red-500/10 text-red-500 rounded text-sm">
                            {student.risk_count} riesgos
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-[var(--text-primary)]">
              Analiticas de Aprendizaje
            </h2>

            {analytics ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {analytics.total_students}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Estudiantes</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {analytics.total_sessions}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Sesiones</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {Math.round(analytics.avg_session_duration)} min
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Duracion Promedio</div>
                  </div>
                  <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                    <div className="text-2xl font-bold text-[var(--text-primary)]">
                      {analytics.period}
                    </div>
                    <div className="text-sm text-[var(--text-muted)]">Periodo</div>
                  </div>
                </div>

                {/* Agent Usage */}
                {analytics.most_used_agents.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-[var(--text-primary)] mb-3">
                      Uso de Agentes IA
                    </h4>
                    <div className="space-y-3">
                      {analytics.most_used_agents.map((agent) => (
                        <div key={agent.agent} className="space-y-1">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-[var(--text-primary)]">{agent.agent}</span>
                            <span className="text-[var(--text-muted)]">
                              {agent.usage_count} usos | {agent.avg_satisfaction.toFixed(1)}/5.0
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
                )}

                {/* Competency Trends */}
                {analytics.competency_trends.length > 0 && (
                  <div>
                    <h4 className="text-md font-medium text-[var(--text-primary)] mb-3">
                      Tendencias de Competencias
                    </h4>
                    <div className="bg-[var(--bg-secondary)] rounded-lg p-4">
                      <div className="space-y-2">
                        {analytics.competency_trends.slice(0, 5).map((trend) => (
                          <div key={`${trend.date}-${trend.competency}`} className="flex items-center justify-between">
                            <span className="text-sm text-[var(--text-secondary)]">
                              {trend.date} - {trend.competency}
                            </span>
                            <span className="text-sm font-medium text-[var(--text-primary)]">
                              {trend.avg_score.toFixed(1)}/10
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-[var(--text-muted)]">
                <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Cargando analiticas...</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Export History */}
      <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
        <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
          Historial de Exportaciones
        </h2>

        {exportHistory.length === 0 ? (
          <div className="text-center py-8 text-[var(--text-muted)]">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No hay exportaciones recientes</p>
          </div>
        ) : (
          <div className="space-y-2">
            {exportHistory.map((item) => (
              <div
                key={item.export_id}
                className="flex items-center justify-between p-3 bg-[var(--bg-secondary)] rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-[var(--text-muted)]" />
                  <div>
                    <div className="text-sm font-medium text-[var(--text-primary)]">
                      {item.type} - {item.format.toUpperCase()}
                    </div>
                    <div className="text-xs text-[var(--text-muted)]">
                      {new Date(item.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded text-xs ${
                    item.status === 'completed' ? 'bg-green-500/10 text-green-500' :
                    item.status === 'pending' ? 'bg-yellow-500/10 text-yellow-500' :
                    'bg-red-500/10 text-red-500'
                  }`}>
                    {item.status}
                  </span>
                  {item.status === 'completed' && item.download_url && (
                    <button
                      onClick={() => window.open(item.download_url, '_blank')}
                      className="p-2 text-[var(--accent-primary)] hover:bg-[var(--accent-primary)]/10 rounded"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
