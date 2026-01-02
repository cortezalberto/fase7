/**
 * InstitutionalRisksPage - Gestion de riesgos institucionales
 *
 * HU-DOC-005: Gestion de Alertas Institucionales
 * HU-DOC-010: Analisis de Efectividad Pedagogica
 *
 * Cortez60: Implementacion de paginas de docente faltantes
 *
 * Backend endpoints utilizados:
 * - GET /api/v1/admin/risks/dashboard - Dashboard de riesgos
 * - GET /api/v1/admin/risks/alerts - Lista de alertas
 * - POST /api/v1/admin/risks/scan - Escanear riesgos
 * - POST /api/v1/admin/risks/alerts/{id}/acknowledge - Reconocer alerta
 * - POST /api/v1/admin/risks/alerts/{id}/resolve - Resolver alerta
 * - POST /api/v1/admin/risks/remediation - Crear plan de remediacion
 * - GET /api/v1/admin/risks/remediation/{id} - Obtener plan
 */
import { useState, useEffect, useCallback } from 'react';
import {
  institutionalRisksService,
  RiskAlert,
  RiskDashboard,
  AlertSeverity,
  AlertStatus,
  CreateRemediationPlanRequest,
} from '../services/api';
import {
  Shield,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Clock,
  Eye,
  RefreshCw,
  Users,
  FileText,
  XCircle,
} from 'lucide-react';

type TabType = 'dashboard' | 'alerts' | 'remediation';

export default function InstitutionalRisksPage() {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [dashboard, setDashboard] = useState<RiskDashboard | null>(null);
  const [alerts, setAlerts] = useState<RiskAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<RiskAlert | null>(null);

  // Filters
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | 'all'>('all');
  const [statusFilter, setStatusFilter] = useState<AlertStatus | 'all'>('all');

  // Remediation modal
  const [showRemediationModal, setShowRemediationModal] = useState(false);
  const [remediationForm, setRemediationForm] = useState({
    student_id: '',
    title: '',
    description: '',
    plan_type: 'standard',
    start_date: '',
    target_end_date: '',
  });

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    try {
      const data = await institutionalRisksService.getDashboard();
      setDashboard(data);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    }
  }, []);

  // Load alerts
  const loadAlerts = useCallback(async () => {
    try {
      const params: { severity?: AlertSeverity; status?: AlertStatus } = {};
      if (severityFilter !== 'all') params.severity = severityFilter;
      if (statusFilter !== 'all') params.status = statusFilter;

      const data = await institutionalRisksService.getAlerts(params);
      setAlerts(data);
    } catch (err) {
      console.error('Error loading alerts:', err);
    }
  }, [severityFilter, statusFilter]);

  // Initial load
  useEffect(() => {
    let isMounted = true;
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        await Promise.all([loadDashboard(), loadAlerts()]);
      } catch {
        if (isMounted) setError('Error al cargar datos de riesgos');
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };
    loadData();
    return () => { isMounted = false; };
  }, [loadDashboard, loadAlerts]);

  // Handle alert actions
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await institutionalRisksService.acknowledgeAlert(alertId);
      await loadAlerts();
    } catch {
      setError('Error al reconocer alerta');
    }
  };

  const handleResolveAlert = async (alertId: string, notes: string) => {
    try {
      await institutionalRisksService.resolveAlert(alertId, notes);
      await loadAlerts();
      setSelectedAlert(null);
    } catch {
      setError('Error al resolver alerta');
    }
  };

  // Handle remediation plan creation
  const handleCreateRemediationPlan = async () => {
    if (!selectedAlert) return;

    try {
      const request: CreateRemediationPlanRequest = {
        student_id: remediationForm.student_id || selectedAlert.affected_students[0] || '',
        alert_ids: [selectedAlert.id],
        plan_type: remediationForm.plan_type,
        title: remediationForm.title,
        description: remediationForm.description,
        actions: [
          {
            description: 'Revisar sesiones del estudiante',
            priority: 'high',
            estimated_effort: '1 hora',
          },
          {
            description: 'Reunion de seguimiento',
            priority: 'medium',
            estimated_effort: '30 minutos',
          },
        ],
        success_metrics: [
          {
            target_metric: 'Reduccion de dependencia IA',
            current_value: 0.8,
            target_value: 0.5,
            measurement_method: 'Promedio de ai_involvement en sesiones',
          },
        ],
        start_date: remediationForm.start_date,
        target_end_date: remediationForm.target_end_date,
      };

      await institutionalRisksService.createRemediationPlan(request);
      setShowRemediationModal(false);
      setRemediationForm({
        student_id: '',
        title: '',
        description: '',
        plan_type: 'standard',
        start_date: '',
        target_end_date: '',
      });
      await loadAlerts();
    } catch {
      setError('Error al crear plan de remediacion');
    }
  };

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'low': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
    }
  };

  const getStatusColor = (status: AlertStatus) => {
    switch (status) {
      case 'pending': return 'bg-red-500/10 text-red-500';
      case 'acknowledged': return 'bg-yellow-500/10 text-yellow-500';
      case 'in_progress': return 'bg-blue-500/10 text-blue-500';
      case 'resolved': return 'bg-green-500/10 text-green-500';
    }
  };

  const tabs = [
    { id: 'dashboard' as TabType, label: 'Dashboard', icon: Shield },
    { id: 'alerts' as TabType, label: 'Alertas', icon: AlertTriangle },
    { id: 'remediation' as TabType, label: 'Remediacion', icon: FileText },
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
            Gestion de Riesgos Institucionales
          </h1>
          <p className="text-[var(--text-secondary)]">
            Monitorea, gestiona y resuelve alertas de riesgo de estudiantes
          </p>
        </div>
        <button
          onClick={() => Promise.all([loadDashboard(), loadAlerts()])}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Actualizar
        </button>
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

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && dashboard && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6 text-white" />
                </div>
                <span className="text-xs px-2 py-1 bg-red-500/10 text-red-500 rounded-full">
                  Total
                </span>
              </div>
              <h3 className="text-3xl font-bold text-[var(--text-primary)]">
                {dashboard.summary.total_alerts}
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">Alertas Totales</p>
            </div>

            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
                  <Clock className="w-6 h-6 text-white" />
                </div>
                <span className="text-xs px-2 py-1 bg-yellow-500/10 text-yellow-500 rounded-full">
                  Pendientes
                </span>
              </div>
              <h3 className="text-3xl font-bold text-[var(--text-primary)]">
                {dashboard.summary.pending_alerts}
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">Por Atender</p>
            </div>

            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-white" />
                </div>
                <span className="text-xs px-2 py-1 bg-red-500/10 text-red-500 rounded-full">
                  Urgente
                </span>
              </div>
              <h3 className="text-3xl font-bold text-[var(--text-primary)]">
                {dashboard.summary.critical_alerts}
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">Alertas Criticas</p>
            </div>

            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <span className="text-xs px-2 py-1 bg-green-500/10 text-green-500 rounded-full">
                  Esta semana
                </span>
              </div>
              <h3 className="text-3xl font-bold text-[var(--text-primary)]">
                {dashboard.summary.resolved_this_week}
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">Resueltas</p>
            </div>
          </div>

          {/* Alerts by Severity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Alertas por Severidad
              </h3>
              <div className="space-y-3">
                {Object.entries(dashboard.alerts_by_severity).map(([severity, count]) => (
                  <div key={severity} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${
                        severity === 'critical' ? 'bg-red-500' :
                        severity === 'high' ? 'bg-orange-500' :
                        severity === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                      }`} />
                      <span className="text-[var(--text-secondary)] capitalize">{severity}</span>
                    </div>
                    <span className="font-medium text-[var(--text-primary)]">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
                Alertas por Tipo
              </h3>
              <div className="space-y-3">
                {Object.entries(dashboard.alerts_by_type).slice(0, 5).map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-[var(--text-secondary)]">{type}</span>
                    <span className="font-medium text-[var(--text-primary)]">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Recent Alerts */}
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Alertas Recientes
            </h3>
            {dashboard.recent_alerts.length === 0 ? (
              <div className="text-center py-8 text-[var(--text-muted)]">
                <Shield className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No hay alertas recientes</p>
              </div>
            ) : (
              <div className="space-y-3">
                {dashboard.recent_alerts.slice(0, 5).map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-lg border ${getSeverityColor(alert.severity)}`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-[var(--text-primary)]">
                            {alert.title}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(alert.status)}`}>
                            {alert.status}
                          </span>
                        </div>
                        <p className="text-sm text-[var(--text-secondary)] line-clamp-1">
                          {alert.description}
                        </p>
                      </div>
                      <button
                        onClick={() => setSelectedAlert(alert)}
                        className="p-2 hover:bg-[var(--bg-hover)] rounded"
                      >
                        <Eye className="w-4 h-4 text-[var(--text-muted)]" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div>
              <label className="block text-sm text-[var(--text-muted)] mb-1">Severidad</label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value as AlertSeverity | 'all')}
                className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
              >
                <option value="all">Todas</option>
                <option value="critical">Critica</option>
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Baja</option>
              </select>
            </div>

            <div>
              <label className="block text-sm text-[var(--text-muted)] mb-1">Estado</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value as AlertStatus | 'all')}
                className="px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
              >
                <option value="all">Todos</option>
                <option value="pending">Pendiente</option>
                <option value="acknowledged">Reconocida</option>
                <option value="in_progress">En Progreso</option>
                <option value="resolved">Resuelta</option>
              </select>
            </div>
          </div>

          {/* Alerts List */}
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] overflow-hidden">
            {alerts.length === 0 ? (
              <div className="text-center py-12 text-[var(--text-muted)]">
                <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No hay alertas con los filtros seleccionados</p>
              </div>
            ) : (
              <div className="divide-y divide-[var(--border-color)]">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-4 hover:bg-[var(--bg-hover)] transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${
                        alert.severity === 'critical' ? 'bg-red-500/10 text-red-500' :
                        alert.severity === 'high' ? 'bg-orange-500/10 text-orange-500' :
                        alert.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
                        'bg-blue-500/10 text-blue-500'
                      }`}>
                        <AlertTriangle className="w-5 h-5" />
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-[var(--text-primary)]">
                            {alert.title}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${getSeverityColor(alert.severity)}`}>
                            {alert.severity}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(alert.status)}`}>
                            {alert.status}
                          </span>
                        </div>
                        <p className="text-sm text-[var(--text-secondary)] mb-2">
                          {alert.description}
                        </p>
                        <div className="flex items-center gap-4 text-xs text-[var(--text-muted)]">
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {alert.affected_students.length} estudiantes
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(alert.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {alert.status === 'pending' && (
                          <button
                            onClick={() => handleAcknowledgeAlert(alert.id)}
                            className="px-3 py-1 text-sm bg-yellow-500/10 text-yellow-500 rounded hover:bg-yellow-500/20"
                          >
                            Reconocer
                          </button>
                        )}
                        {alert.status !== 'resolved' && (
                          <button
                            onClick={() => setSelectedAlert(alert)}
                            className="px-3 py-1 text-sm bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] rounded hover:bg-[var(--accent-primary)]/20"
                          >
                            Gestionar
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Remediation Tab */}
      {activeTab === 'remediation' && (
        <div className="space-y-6">
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6">
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-4">
              Planes de Remediacion
            </h3>
            <p className="text-[var(--text-secondary)] mb-6">
              Los planes de remediacion se crean a partir de alertas activas.
              Selecciona una alerta en la pestana "Alertas" para crear un plan.
            </p>
            <div className="text-center py-8 text-[var(--text-muted)]">
              <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Selecciona una alerta para crear un plan de remediacion</p>
            </div>
          </div>
        </div>
      )}

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                    {selectedAlert.title}
                  </h2>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full uppercase ${getSeverityColor(selectedAlert.severity)}`}>
                      {selectedAlert.severity}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(selectedAlert.status)}`}>
                      {selectedAlert.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAlert(null)}
                  className="p-2 hover:bg-[var(--bg-hover)] rounded"
                >
                  <XCircle className="w-5 h-5 text-[var(--text-muted)]" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Descripcion</h4>
                  <p className="text-[var(--text-secondary)]">{selectedAlert.description}</p>
                </div>

                <div>
                  <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Estudiantes Afectados</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedAlert.affected_students.map((student) => (
                      <span key={student} className="px-2 py-1 bg-[var(--bg-secondary)] rounded text-sm">
                        {student}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedAlert.recommendations.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-[var(--text-muted)] mb-1">Recomendaciones</h4>
                    <ul className="space-y-1">
                      {selectedAlert.recommendations.map((rec) => (
                        <li key={`rec-${rec.slice(0, 20).replace(/\s/g, '-')}`} className="text-sm text-[var(--text-secondary)] flex items-start gap-2">
                          <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                          {rec}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex gap-3 pt-4 border-t border-[var(--border-color)]">
                  {selectedAlert.status === 'pending' && (
                    <button
                      onClick={() => handleAcknowledgeAlert(selectedAlert.id)}
                      className="flex-1 px-4 py-2 bg-yellow-500/10 text-yellow-500 rounded-lg hover:bg-yellow-500/20"
                    >
                      Reconocer Alerta
                    </button>
                  )}
                  <button
                    onClick={() => {
                      setRemediationForm({
                        ...remediationForm,
                        student_id: selectedAlert.affected_students[0] || '',
                        title: `Plan de remediacion: ${selectedAlert.title}`,
                      });
                      setShowRemediationModal(true);
                    }}
                    className="flex-1 px-4 py-2 bg-[var(--accent-primary)]/10 text-[var(--accent-primary)] rounded-lg hover:bg-[var(--accent-primary)]/20"
                  >
                    Crear Plan de Remediacion
                  </button>
                  {selectedAlert.status !== 'resolved' && (
                    <button
                      onClick={() => handleResolveAlert(selectedAlert.id, 'Resuelta por docente')}
                      className="flex-1 px-4 py-2 bg-green-500/10 text-green-500 rounded-lg hover:bg-green-500/20"
                    >
                      Marcar como Resuelta
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Remediation Plan Modal */}
      {showRemediationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] max-w-lg w-full">
            <div className="p-6">
              <h2 className="text-xl font-semibold text-[var(--text-primary)] mb-4">
                Crear Plan de Remediacion
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Titulo del Plan
                  </label>
                  <input
                    type="text"
                    value={remediationForm.title}
                    onChange={(e) => setRemediationForm({ ...remediationForm, title: e.target.value })}
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Descripcion
                  </label>
                  <textarea
                    value={remediationForm.description}
                    onChange={(e) => setRemediationForm({ ...remediationForm, description: e.target.value })}
                    rows={3}
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      Fecha Inicio
                    </label>
                    <input
                      type="date"
                      value={remediationForm.start_date}
                      onChange={(e) => setRemediationForm({ ...remediationForm, start_date: e.target.value })}
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      Fecha Objetivo
                    </label>
                    <input
                      type="date"
                      value={remediationForm.target_end_date}
                      onChange={(e) => setRemediationForm({ ...remediationForm, target_end_date: e.target.value })}
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => setShowRemediationModal(false)}
                    className="flex-1 px-4 py-2 bg-[var(--bg-secondary)] text-[var(--text-secondary)] rounded-lg hover:bg-[var(--bg-hover)]"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleCreateRemediationPlan}
                    className="flex-1 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90"
                  >
                    Crear Plan
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
