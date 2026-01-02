/**
 * ActivityManagementPage - Gestion de actividades para docentes
 *
 * HU-DOC-006: Administracion de Actividades
 * HU-DOC-007: Configuracion de Ejercicios
 *
 * Cortez60: Implementacion de paginas de docente faltantes
 *
 * Backend endpoints utilizados:
 * - GET /api/v1/activities - Listar actividades
 * - POST /api/v1/activities - Crear actividad
 * - PUT /api/v1/activities/{id} - Actualizar actividad
 * - POST /api/v1/activities/{id}/publish - Publicar actividad
 * - POST /api/v1/activities/{id}/archive - Archivar actividad
 * - DELETE /api/v1/activities/{id} - Eliminar actividad
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { activitiesService, ActivityListParams } from '../services/api';
import type { ActivityResponse, ActivityCreate, ActivityUpdate, PolicyConfig } from '../types/api.types';
import { ActivityDifficulty, HelpLevel } from '../types/domain/enums';
import {
  BookOpen,
  Plus,
  Edit,
  Trash2,
  Archive,
  Send,
  Copy,
  Search,
  Clock,
  XCircle,
  RefreshCw,
  MoreVertical,
} from 'lucide-react';

type TabType = 'all' | 'draft' | 'active' | 'archived';

export default function ActivityManagementPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [selectedActivity, setSelectedActivity] = useState<ActivityResponse | null>(null);

  // Default policy config matching PolicyConfig type
  const defaultPolicies: PolicyConfig = {
    max_help_level: HelpLevel.MEDIO,
    block_complete_solutions: true,
    require_justification: true,
    allow_code_snippets: true,
    risk_thresholds: { cognitive_delegation: 0.7, ai_dependency: 0.6 },
  };

  // Form state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState<Partial<ActivityCreate>>({
    activity_id: '',
    title: '',
    description: '',
    instructions: '',
    subject: '',
    difficulty: ActivityDifficulty.INICIAL,
    estimated_duration_minutes: 60,
    tags: [],
    policies: defaultPolicies,
    evaluation_criteria: [],
  });

  // Filters
  const [searchQuery, setSearchQuery] = useState('');

  // Load activities
  const loadActivities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: ActivityListParams = {};
      if (user?.id) {
        params.teacher_id = user.id;
      }
      if (activeTab !== 'all') {
        params.status = activeTab;
      }

      const response = await activitiesService.list(params);
      setActivities(response.data || []);
    } catch (err) {
      console.error('Error loading activities:', err);
      setError('Error al cargar actividades');
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, activeTab]);

  useEffect(() => {
    loadActivities();
  }, [loadActivities]);

  // Create activity
  const handleCreateActivity = async () => {
    if (!formData.activity_id || !formData.title || !formData.instructions) {
      setError('Por favor complete los campos requeridos');
      return;
    }

    try {
      const createData: ActivityCreate = {
        activity_id: formData.activity_id!,
        title: formData.title!,
        instructions: formData.instructions!,
        teacher_id: user?.id || '',
        description: formData.description,
        subject: formData.subject,
        difficulty: formData.difficulty,
        estimated_duration_minutes: formData.estimated_duration_minutes,
        tags: formData.tags,
        policies: formData.policies || defaultPolicies,
        evaluation_criteria: formData.evaluation_criteria,
      };

      await activitiesService.create(createData);
      setShowCreateModal(false);
      resetForm();
      await loadActivities();
    } catch {
      setError('Error al crear actividad');
    }
  };

  // Update activity
  const handleUpdateActivity = async () => {
    if (!selectedActivity) return;

    try {
      const updateData: ActivityUpdate = {
        title: formData.title,
        description: formData.description,
        instructions: formData.instructions,
        subject: formData.subject,
        difficulty: formData.difficulty,
        estimated_duration_minutes: formData.estimated_duration_minutes,
        tags: formData.tags,
        policies: formData.policies || defaultPolicies,
        evaluation_criteria: formData.evaluation_criteria,
      };

      await activitiesService.update(selectedActivity.activity_id, updateData);
      setShowEditModal(false);
      setSelectedActivity(null);
      resetForm();
      await loadActivities();
    } catch {
      setError('Error al actualizar actividad');
    }
  };

  // Publish activity
  const handlePublishActivity = async (activityId: string) => {
    try {
      await activitiesService.publish(activityId);
      await loadActivities();
    } catch {
      setError('Error al publicar actividad');
    }
  };

  // Archive activity
  const handleArchiveActivity = async (activityId: string) => {
    try {
      await activitiesService.archive(activityId);
      await loadActivities();
    } catch {
      setError('Error al archivar actividad');
    }
  };

  // Delete activity
  const handleDeleteActivity = async (activityId: string) => {
    if (!confirm('Esta seguro de eliminar esta actividad?')) return;

    try {
      await activitiesService.remove(activityId);
      await loadActivities();
    } catch {
      setError('Error al eliminar actividad');
    }
  };

  // Clone activity
  const handleCloneActivity = async (activity: ActivityResponse) => {
    const newId = `${activity.activity_id}_copy_${Date.now()}`;
    try {
      await activitiesService.clone(activity.activity_id, newId, user?.id || '');
      await loadActivities();
    } catch {
      setError('Error al clonar actividad');
    }
  };

  // Open edit modal
  const openEditModal = (activity: ActivityResponse) => {
    setSelectedActivity(activity);
    // Map string difficulty to enum
    const difficultyMap: Record<string, ActivityDifficulty> = {
      'INICIAL': ActivityDifficulty.INICIAL,
      'INTERMEDIO': ActivityDifficulty.INTERMEDIO,
      'AVANZADO': ActivityDifficulty.AVANZADO,
    };
    setFormData({
      activity_id: activity.activity_id,
      title: activity.title,
      description: activity.description || '',
      instructions: activity.instructions,
      subject: activity.subject || '',
      difficulty: difficultyMap[activity.difficulty || 'INICIAL'] || ActivityDifficulty.INICIAL,
      estimated_duration_minutes: activity.estimated_duration_minutes || 60,
      tags: activity.tags || [],
      policies: activity.policies || defaultPolicies,
      evaluation_criteria: activity.evaluation_criteria || [],
    });
    setShowEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      activity_id: '',
      title: '',
      description: '',
      instructions: '',
      subject: '',
      difficulty: ActivityDifficulty.INICIAL,
      estimated_duration_minutes: 60,
      tags: [],
      policies: defaultPolicies,
      evaluation_criteria: [],
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/10 text-green-500';
      case 'draft': return 'bg-yellow-500/10 text-yellow-500';
      case 'archived': return 'bg-gray-500/10 text-gray-500';
      default: return 'bg-blue-500/10 text-blue-500';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'INICIAL': return 'bg-green-500/10 text-green-500';
      case 'INTERMEDIO': return 'bg-yellow-500/10 text-yellow-500';
      case 'AVANZADO': return 'bg-red-500/10 text-red-500';
      default: return 'bg-gray-500/10 text-gray-500';
    }
  };

  // FIX Cortez60: Memoize filtered activities to avoid recalculation on each render
  const filteredActivities = useMemo(() => {
    return activities.filter(activity => {
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          activity.title.toLowerCase().includes(query) ||
          activity.activity_id.toLowerCase().includes(query) ||
          activity.subject?.toLowerCase().includes(query)
        );
      }
      return true;
    });
  }, [activities, searchQuery]);

  const tabs = [
    { id: 'all' as TabType, label: 'Todas' },
    { id: 'draft' as TabType, label: 'Borrador' },
    { id: 'active' as TabType, label: 'Activas' },
    { id: 'archived' as TabType, label: 'Archivadas' },
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
            Gestion de Actividades
          </h1>
          <p className="text-[var(--text-secondary)]">
            Crea, edita y administra actividades para tus estudiantes
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          Nueva Actividad
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

      {/* Tabs and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex gap-2 border-b border-[var(--border-color)] sm:border-b-0">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 border-b-2 sm:border-b-0 sm:rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'border-[var(--accent-primary)] text-[var(--accent-primary)] sm:bg-[var(--accent-primary)]/10'
                  : 'border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Buscar actividades..."
            className="w-full pl-10 pr-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
          />
        </div>

        <button
          onClick={loadActivities}
          className="flex items-center gap-2 px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg hover:bg-[var(--bg-hover)]"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Activities Grid */}
      {filteredActivities.length === 0 ? (
        <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-12 text-center">
          <BookOpen className="w-12 h-12 mx-auto mb-4 text-[var(--text-muted)] opacity-50" />
          <p className="text-lg font-medium text-[var(--text-primary)] mb-2">
            No hay actividades
          </p>
          <p className="text-[var(--text-secondary)] mb-6">
            Crea tu primera actividad para comenzar
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90"
          >
            <Plus className="w-5 h-5" />
            Crear Actividad
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredActivities.map((activity) => (
            <div
              key={activity.activity_id}
              className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6 hover:border-[var(--border-light)] transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(activity.status)}`}>
                    {activity.status}
                  </span>
                  {activity.difficulty && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getDifficultyColor(activity.difficulty)}`}>
                      {activity.difficulty}
                    </span>
                  )}
                </div>
                <div className="relative group">
                  <button className="p-1 hover:bg-[var(--bg-hover)] rounded">
                    <MoreVertical className="w-4 h-4 text-[var(--text-muted)]" />
                  </button>
                  <div className="absolute right-0 top-full mt-1 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 min-w-[150px]">
                    <button
                      onClick={() => openEditModal(activity)}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                    >
                      <Edit className="w-4 h-4" />
                      Editar
                    </button>
                    <button
                      onClick={() => handleCloneActivity(activity)}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                    >
                      <Copy className="w-4 h-4" />
                      Clonar
                    </button>
                    {activity.status === 'draft' && (
                      <button
                        onClick={() => handlePublishActivity(activity.activity_id)}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-green-500 hover:bg-[var(--bg-hover)]"
                      >
                        <Send className="w-4 h-4" />
                        Publicar
                      </button>
                    )}
                    {activity.status === 'active' && (
                      <button
                        onClick={() => handleArchiveActivity(activity.activity_id)}
                        className="w-full flex items-center gap-2 px-4 py-2 text-sm text-yellow-500 hover:bg-[var(--bg-hover)]"
                      >
                        <Archive className="w-4 h-4" />
                        Archivar
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteActivity(activity.activity_id)}
                      className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-[var(--bg-hover)]"
                    >
                      <Trash2 className="w-4 h-4" />
                      Eliminar
                    </button>
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
                {activity.title}
              </h3>

              <p className="text-sm text-[var(--text-secondary)] mb-4 line-clamp-2">
                {activity.description || activity.instructions}
              </p>

              <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)]">
                {activity.subject && (
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    {activity.subject}
                  </span>
                )}
                {activity.estimated_duration_minutes && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {activity.estimated_duration_minutes} min
                  </span>
                )}
              </div>

              {activity.tags && activity.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {activity.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs text-[var(--text-muted)]">
                      {tag}
                    </span>
                  ))}
                  {activity.tags.length > 3 && (
                    <span className="px-2 py-0.5 bg-[var(--bg-tertiary)] rounded text-xs text-[var(--text-muted)]">
                      +{activity.tags.length - 3}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  Nueva Actividad
                </h2>
                <button
                  onClick={() => { setShowCreateModal(false); resetForm(); }}
                  className="p-2 hover:bg-[var(--bg-hover)] rounded"
                >
                  <XCircle className="w-5 h-5 text-[var(--text-muted)]" />
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      ID de Actividad *
                    </label>
                    <input
                      type="text"
                      value={formData.activity_id}
                      onChange={(e) => setFormData({ ...formData, activity_id: e.target.value })}
                      placeholder="ej: prog2_tp1_colas"
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      Materia
                    </label>
                    <input
                      type="text"
                      value={formData.subject}
                      onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                      placeholder="ej: Programacion II"
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Titulo *
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Titulo de la actividad"
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Descripcion
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={2}
                    placeholder="Descripcion breve de la actividad"
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Instrucciones *
                  </label>
                  <textarea
                    value={formData.instructions}
                    onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                    rows={4}
                    placeholder="Instrucciones detalladas para los estudiantes"
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      Dificultad
                    </label>
                    <select
                      value={formData.difficulty}
                      onChange={(e) => setFormData({ ...formData, difficulty: e.target.value as ActivityDifficulty })}
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    >
                      <option value={ActivityDifficulty.INICIAL}>Inicial</option>
                      <option value={ActivityDifficulty.INTERMEDIO}>Intermedio</option>
                      <option value={ActivityDifficulty.AVANZADO}>Avanzado</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                      Duracion Estimada (min)
                    </label>
                    <input
                      type="number"
                      value={formData.estimated_duration_minutes}
                      onChange={(e) => setFormData({ ...formData, estimated_duration_minutes: parseInt(e.target.value) })}
                      min={5}
                      max={480}
                      className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Etiquetas (separadas por coma)
                  </label>
                  <input
                    type="text"
                    value={formData.tags?.join(', ') || ''}
                    onChange={(e) => setFormData({ ...formData, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                    placeholder="ej: estructuras, colas, fifo"
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div className="border-t border-[var(--border-color)] pt-4">
                  <h4 className="text-sm font-medium text-[var(--text-primary)] mb-3">Politicas de IA</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm text-[var(--text-secondary)] mb-1">
                        Nivel Maximo de Ayuda
                      </label>
                      <select
                        value={formData.policies?.max_help_level || HelpLevel.MEDIO}
                        onChange={(e) => setFormData({
                          ...formData,
                          policies: { ...formData.policies!, max_help_level: e.target.value as HelpLevel }
                        })}
                        className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                      >
                        <option value={HelpLevel.MINIMO}>Minimo</option>
                        <option value={HelpLevel.BAJO}>Bajo</option>
                        <option value={HelpLevel.MEDIO}>Medio</option>
                        <option value={HelpLevel.ALTO}>Alto</option>
                      </select>
                    </div>
                    <div className="flex flex-col justify-end">
                      <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                        <input
                          type="checkbox"
                          checked={formData.policies?.require_justification ?? true}
                          onChange={(e) => setFormData({
                            ...formData,
                            policies: { ...formData.policies!, require_justification: e.target.checked }
                          })}
                          className="rounded"
                        />
                        Requerir justificacion
                      </label>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4 mt-3">
                    <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                      <input
                        type="checkbox"
                        checked={formData.policies?.block_complete_solutions ?? true}
                        onChange={(e) => setFormData({
                          ...formData,
                          policies: { ...formData.policies!, block_complete_solutions: e.target.checked }
                        })}
                        className="rounded"
                      />
                      Bloquear soluciones completas
                    </label>
                    <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
                      <input
                        type="checkbox"
                        checked={formData.policies?.allow_code_snippets ?? true}
                        onChange={(e) => setFormData({
                          ...formData,
                          policies: { ...formData.policies!, allow_code_snippets: e.target.checked }
                        })}
                        className="rounded"
                      />
                      Permitir fragmentos de codigo
                    </label>
                  </div>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => { setShowCreateModal(false); resetForm(); }}
                    className="flex-1 px-4 py-2 bg-[var(--bg-secondary)] text-[var(--text-secondary)] rounded-lg hover:bg-[var(--bg-hover)]"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleCreateActivity}
                    className="flex-1 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90"
                  >
                    Crear Actividad
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal - Similar to Create but with Update logic */}
      {showEditModal && selectedActivity && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-[var(--text-primary)]">
                  Editar Actividad
                </h2>
                <button
                  onClick={() => { setShowEditModal(false); setSelectedActivity(null); resetForm(); }}
                  className="p-2 hover:bg-[var(--bg-hover)] rounded"
                >
                  <XCircle className="w-5 h-5 text-[var(--text-muted)]" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    ID de Actividad (no editable)
                  </label>
                  <input
                    type="text"
                    value={formData.activity_id}
                    disabled
                    className="w-full px-4 py-2 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-muted)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Titulo
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-[var(--text-secondary)] mb-1">
                    Instrucciones
                  </label>
                  <textarea
                    value={formData.instructions}
                    onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-2 bg-[var(--bg-secondary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)]"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => { setShowEditModal(false); setSelectedActivity(null); resetForm(); }}
                    className="flex-1 px-4 py-2 bg-[var(--bg-secondary)] text-[var(--text-secondary)] rounded-lg hover:bg-[var(--bg-hover)]"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleUpdateActivity}
                    className="flex-1 px-4 py-2 bg-[var(--accent-primary)] text-white rounded-lg hover:opacity-90"
                  >
                    Guardar Cambios
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
