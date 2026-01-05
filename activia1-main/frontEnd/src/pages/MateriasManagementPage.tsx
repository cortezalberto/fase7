/**
 * MateriasManagementPage - CRUD de materias academicas
 *
 * Permite a profesores:
 * - Listar todas las materias
 * - Crear nuevas materias
 * - Editar materias existentes
 * - Activar/desactivar materias
 * - Eliminar materias (con confirmacion)
 *
 * Cortez79: Implementacion CRUD de materias
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Book, Plus, Edit2, Trash2, Check, X,
  AlertTriangle, Search, RefreshCw
} from 'lucide-react';
import { academicService } from '@/services/api';
import type {
  MateriaCreate,
  MateriaUpdate,
  MateriaConUnidades,
} from '@/types';

// ==================== Tipos ====================

interface MateriaFormData {
  code: string;
  name: string;
  description: string;
  language: 'python' | 'java';
  total_units: number;
  is_active: boolean;
}

const EMPTY_FORM: MateriaFormData = {
  code: '',
  name: '',
  description: '',
  language: 'python',
  total_units: 0,
  is_active: true,
};

// ==================== Componente de Formulario ====================

interface MateriaFormProps {
  initialData?: MateriaFormData;
  isEditing: boolean;
  onSave: (data: MateriaFormData) => Promise<void>;
  onCancel: () => void;
}

function MateriaForm({ initialData, isEditing, onSave, onCancel }: MateriaFormProps) {
  const [formData, setFormData] = useState<MateriaFormData>(initialData || EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validaciones
    if (!formData.code.trim()) {
      setError('El codigo es obligatorio');
      return;
    }
    if (!formData.name.trim()) {
      setError('El nombre es obligatorio');
      return;
    }
    if (!/^[A-Z0-9_]+$/.test(formData.code)) {
      setError('El codigo solo puede contener letras mayusculas, numeros y guiones bajos');
      return;
    }

    setSaving(true);
    try {
      await onSave(formData);
    } catch (err) {
      // Handle different error formats: { error: { message } } or { detail } or Error
      const apiError = err as { error?: { message?: string }; detail?: string };
      const errorMessage = apiError?.error?.message || apiError?.detail ||
        (err instanceof Error ? err.message : 'Error al guardar la materia');
      setError(errorMessage);
      if (import.meta.env.DEV) console.error('Save error:', err);
    } finally {
      setSaving(false);
    }
  };

  // Cortez79: Input styles compatible with dark/light theme
  const inputClassName = "w-full p-3 border border-[var(--border-color)] rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-colors";
  const labelClassName = "block text-sm font-medium text-[var(--text-secondary)] mb-1";

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[var(--bg-card)] rounded-xl shadow-xl w-full max-w-lg mx-4 border border-[var(--border-color)]">
        <div className="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
          <h2 className="text-xl font-semibold flex items-center gap-2 text-[var(--text-primary)]">
            <Book className="w-5 h-5 text-indigo-500" />
            {isEditing ? 'Editar Materia' : 'Nueva Materia'}
          </h2>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-[var(--bg-hover)] rounded-lg transition-colors text-[var(--text-secondary)]"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-4 h-4" />
              {error}
            </div>
          )}

          <div>
            <label className={labelClassName}>
              Codigo *
            </label>
            <input
              type="text"
              value={formData.code}
              onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
              disabled={isEditing}
              placeholder="PROG1, PYTHON, JAVA"
              className={`${inputClassName} ${isEditing ? 'opacity-60 cursor-not-allowed' : ''}`}
              required
            />
            <p className="text-xs text-[var(--text-muted)] mt-1">
              Solo mayusculas, numeros y guiones bajos. No se puede cambiar despues.
            </p>
          </div>

          <div>
            <label className={labelClassName}>
              Nombre *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Programacion 1"
              className={inputClassName}
              required
            />
          </div>

          <div>
            <label className={labelClassName}>
              Descripcion
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Descripcion de la materia..."
              rows={3}
              className={`${inputClassName} resize-none`}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClassName}>
                Lenguaje *
              </label>
              <select
                value={formData.language}
                onChange={(e) => setFormData({ ...formData, language: e.target.value as 'python' | 'java' })}
                className={inputClassName}
              >
                <option value="python">Python</option>
                <option value="java">Java</option>
              </select>
            </div>

            <div>
              <label className={labelClassName}>
                Total Unidades
              </label>
              <input
                type="number"
                min="0"
                value={formData.total_units}
                onChange={(e) => setFormData({ ...formData, total_units: parseInt(e.target.value, 10) || 0 })}
                className={inputClassName}
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="is_active"
              checked={formData.is_active}
              onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
              className="w-4 h-4 text-indigo-600 rounded border-[var(--border-color)] bg-[var(--bg-tertiary)]"
            />
            <label htmlFor="is_active" className="text-sm text-[var(--text-secondary)]">
              Materia activa (visible para estudiantes)
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-[var(--border-color)]">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--bg-tertiary)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Guardando...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" />
                  {isEditing ? 'Actualizar' : 'Crear'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ==================== Dialogo de Confirmacion ====================

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmText: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function ConfirmDialog({ title, message, confirmText, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[var(--bg-card)] rounded-xl shadow-xl w-full max-w-md mx-4 p-6 border border-[var(--border-color)]">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-red-500/20 rounded-full">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>
          <h3 className="text-lg font-semibold text-[var(--text-primary)]">{title}</h3>
        </div>
        <p className="text-[var(--text-secondary)] mb-6">{message}</p>
        <div className="flex justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-[var(--text-secondary)] bg-[var(--bg-tertiary)] rounded-lg hover:bg-[var(--bg-hover)] transition-colors"
          >
            Cancelar
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

// ==================== Componente Principal ====================

export default function MateriasManagementPage() {
  const [materias, setMaterias] = useState<MateriaConUnidades[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showInactive, setShowInactive] = useState(false);

  // Estado de modales
  const [showForm, setShowForm] = useState(false);
  const [editingMateria, setEditingMateria] = useState<MateriaConUnidades | null>(null);
  const [deletingMateria, setDeletingMateria] = useState<MateriaConUnidades | null>(null);

  // Cargar materias
  const loadMaterias = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await academicService.getMaterias({
        solo_activas: !showInactive,
        incluir_unidades: true,
      });
      // FIX Cortez79: Ensure data is always an array
      // The API response might be wrapped in a 'data' property
      const materiasArray = Array.isArray(data) ? data : (data as unknown as { data: MateriaConUnidades[] })?.data || [];
      setMaterias(materiasArray);
    } catch (err) {
      const apiError = err as { error?: { message?: string }; detail?: string };
      const errorMessage = apiError?.error?.message || apiError?.detail ||
        (err instanceof Error ? err.message : 'Error al cargar las materias');
      setError(errorMessage);
      if (import.meta.env.DEV) console.error('Error loading materias:', err);
    } finally {
      setLoading(false);
    }
  }, [showInactive]);

  useEffect(() => {
    loadMaterias();
  }, [loadMaterias]);

  // Filtrar materias por busqueda
  // FIX Cortez79: Add fallback to empty array to prevent filter on undefined
  const filteredMaterias = (materias || []).filter((m) => {
    const search = searchTerm.toLowerCase();
    return (
      m.code.toLowerCase().includes(search) ||
      m.name.toLowerCase().includes(search) ||
      m.description?.toLowerCase().includes(search)
    );
  });

  // Handlers
  const handleCreate = async (data: MateriaFormData) => {
    const createData: MateriaCreate = {
      code: data.code,
      name: data.name,
      description: data.description || undefined,
      language: data.language,
      total_units: data.total_units,
      is_active: data.is_active,
    };
    await academicService.createMateria(createData);
    setShowForm(false);
    await loadMaterias();
  };

  const handleUpdate = async (data: MateriaFormData) => {
    if (!editingMateria) return;
    const updateData: MateriaUpdate = {
      name: data.name,
      description: data.description || undefined,
      total_units: data.total_units,
      is_active: data.is_active,
    };
    await academicService.updateMateria(editingMateria.code, updateData);
    setEditingMateria(null);
    await loadMaterias();
  };

  const handleDelete = async () => {
    if (!deletingMateria) return;
    try {
      await academicService.deleteMateria(deletingMateria.code);
      setDeletingMateria(null);
      await loadMaterias();
    } catch (err) {
      const apiError = err as { error?: { message?: string }; detail?: string };
      const errorMessage = apiError?.error?.message || apiError?.detail ||
        (err instanceof Error ? err.message : 'Error al eliminar la materia');
      setError(errorMessage);
      setDeletingMateria(null);
    }
  };

  const handleToggleActive = async (materia: MateriaConUnidades) => {
    try {
      await academicService.toggleMateriaActive(materia.code, !materia.is_active);
      await loadMaterias();
    } catch (err) {
      const apiError = err as { error?: { message?: string }; detail?: string };
      const errorMessage = apiError?.error?.message || apiError?.detail ||
        (err instanceof Error ? err.message : 'Error al cambiar estado de la materia');
      setError(errorMessage);
    }
  };

  // Render
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] flex items-center gap-2">
            <Book className="w-7 h-7 text-indigo-600" />
            Gestion de Materias
          </h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Administra las materias y sus configuraciones
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Nueva Materia
        </button>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex-1 relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            placeholder="Buscar por codigo, nombre o descripcion..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[var(--border-color)] rounded-lg bg-[var(--bg-tertiary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={showInactive}
            onChange={(e) => setShowInactive(e.target.checked)}
            className="w-4 h-4 text-indigo-600 rounded border-[var(--border-color)] bg-[var(--bg-tertiary)]"
          />
          <span className="text-sm text-[var(--text-secondary)]">Mostrar inactivas</span>
        </label>
        <button
          onClick={loadMaterias}
          className="p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] rounded-lg transition-colors"
          title="Recargar"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2 text-red-400">
          <AlertTriangle className="w-5 h-5" />
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-auto p-1 hover:bg-red-500/20 rounded"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
        </div>
      )}

      {/* Lista de materias */}
      {!loading && (
        <div className="bg-[var(--bg-card)] rounded-xl shadow-sm border border-[var(--border-color)] overflow-hidden">
          <table className="w-full">
            <thead className="bg-[var(--bg-tertiary)] border-b border-[var(--border-color)]">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Codigo</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Nombre</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Lenguaje</th>
                <th className="text-center px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Unidades</th>
                <th className="text-center px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Estado</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-[var(--text-secondary)]">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-color)]">
              {filteredMaterias.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-[var(--text-muted)]">
                    {searchTerm
                      ? 'No se encontraron materias con esa busqueda'
                      : 'No hay materias registradas'}
                  </td>
                </tr>
              ) : (
                filteredMaterias.map((materia) => (
                  <tr key={materia.code} className="hover:bg-[var(--bg-hover)]">
                    <td className="px-4 py-3">
                      <code className="px-2 py-1 bg-indigo-500/10 text-indigo-400 rounded text-sm font-mono">
                        {materia.code}
                      </code>
                    </td>
                    <td className="px-4 py-3">
                      <div>
                        <div className="font-medium text-[var(--text-primary)]">{materia.name}</div>
                        {materia.description && (
                          <div className="text-sm text-[var(--text-muted)] truncate max-w-xs">
                            {materia.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        materia.language === 'python'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-orange-500/20 text-orange-400'
                      }`}>
                        {materia.language}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-[var(--text-secondary)]">
                        {materia.unidades?.length || materia.total_units || 0}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleToggleActive(materia)}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          materia.is_active
                            ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                            : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                        }`}
                      >
                        {materia.is_active ? 'Activa' : 'Inactiva'}
                      </button>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => setEditingMateria(materia)}
                          className="p-2 text-[var(--text-secondary)] hover:bg-indigo-500/10 hover:text-indigo-400 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setDeletingMateria(materia)}
                          className="p-2 text-[var(--text-secondary)] hover:bg-red-500/10 hover:text-red-400 rounded-lg transition-colors"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Stats */}
      {!loading && materias && materias.length > 0 && (
        <div className="mt-4 flex items-center gap-4 text-sm text-[var(--text-muted)]">
          <span>Total: {materias.length} materias</span>
          <span>|</span>
          <span>Activas: {materias.filter(m => m.is_active).length}</span>
          <span>|</span>
          <span>Inactivas: {materias.filter(m => !m.is_active).length}</span>
        </div>
      )}

      {/* Modal de formulario (crear) */}
      {showForm && (
        <MateriaForm
          isEditing={false}
          onSave={handleCreate}
          onCancel={() => setShowForm(false)}
        />
      )}

      {/* Modal de formulario (editar) */}
      {editingMateria && (
        <MateriaForm
          isEditing={true}
          initialData={{
            code: editingMateria.code,
            name: editingMateria.name,
            description: editingMateria.description || '',
            language: editingMateria.language as 'python' | 'java',
            total_units: editingMateria.total_units,
            is_active: editingMateria.is_active,
          }}
          onSave={handleUpdate}
          onCancel={() => setEditingMateria(null)}
        />
      )}

      {/* Dialogo de confirmacion de eliminacion */}
      {deletingMateria && (
        <ConfirmDialog
          title="Eliminar Materia"
          message={`¿Esta seguro de eliminar la materia "${deletingMateria.name}" (${deletingMateria.code})? Esta accion eliminara tambien todas las unidades y ejercicios asociados.`}
          confirmText="Eliminar"
          onConfirm={handleDelete}
          onCancel={() => setDeletingMateria(null)}
        />
      )}
    </div>
  );
}
