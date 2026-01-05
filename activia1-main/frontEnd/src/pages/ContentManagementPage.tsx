/**
 * ContentManagementPage - Gestion de contenido academico
 *
 * Permite a profesores gestionar:
 * - Materias y sus metadatos
 * - Unidades con objetivos de aprendizaje
 * - Material teorico (PDF)
 * - Material practico (PDF)
 *
 * Patron: Maestro-Detalle de 3 niveles
 * Materia -> Unidad -> Contenido (Teoria + Practica)
 *
 * Cortez72: Implementacion desde metodologia.md
 * Cortez80: Mejora UI para separar contenido teorico y practico
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Book, FileText, Code, Plus, Trash2, Edit2,
  ChevronRight, Eye, EyeOff, Clock, Target,
  X, BookOpen, Wrench, RefreshCw
} from 'lucide-react';
import { academicService, filesService } from '@/services/api';
import { FileUploader } from '@/components/FileUploader';
import { PDFViewer } from '@/components/PDFViewer';
import type {
  MateriaConUnidades,
  UnidadConEjercicios,
  UnidadCreate,
  ArchivoAdjunto,
} from '@/types';

// ==================== Componentes Auxiliares ====================

// Componente para mostrar breadcrumb de navegacion
interface BreadcrumbProps {
  materia?: MateriaConUnidades;
  unidad?: UnidadConEjercicios;
  onClickMateria?: () => void;
  onClickUnidad?: () => void;
}

function Breadcrumb({ materia, unidad, onClickMateria, onClickUnidad }: BreadcrumbProps) {
  return (
    <div className="flex items-center gap-2 text-sm mb-4 p-3 bg-[var(--bg-tertiary)] rounded-lg">
      <span className="text-[var(--text-muted)]">Navegacion:</span>
      <button
        onClick={onClickMateria}
        className={`px-2 py-1 rounded ${materia ? 'text-indigo-400 hover:bg-indigo-500/20' : 'text-[var(--text-muted)]'}`}
      >
        {materia ? materia.name : 'Seleccionar Materia'}
      </button>
      {materia && (
        <>
          <ChevronRight className="w-4 h-4 text-[var(--text-muted)]" />
          <button
            onClick={onClickUnidad}
            className={`px-2 py-1 rounded ${unidad ? 'text-indigo-400 hover:bg-indigo-500/20' : 'text-[var(--text-muted)]'}`}
          >
            {unidad ? `Unidad ${unidad.numero}: ${unidad.titulo}` : 'Seleccionar Unidad'}
          </button>
        </>
      )}
      {unidad && (
        <>
          <ChevronRight className="w-4 h-4 text-[var(--text-muted)]" />
          <span className="text-green-400 font-medium">Contenido</span>
        </>
      )}
    </div>
  );
}

// Componente para seccion de archivos (teoricos o practicos)
interface ArchivosSectionProps {
  titulo: string;
  descripcion: string;
  icon: React.ReactNode;
  iconColor: string;
  archivos: ArchivoAdjunto[];
  unidadId: string;
  tipoPrefix: string;
  onViewPDF: (url: string, nombre: string) => void;
  onDelete: (id: string) => void;
  onUploadSuccess: (archivo: { id: string; nombre: string; url: string }) => void;
}

function ArchivosSection({
  titulo,
  descripcion,
  icon,
  iconColor,
  archivos,
  unidadId,
  onViewPDF,
  onDelete,
  onUploadSuccess,
}: ArchivosSectionProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <div className="border border-[var(--border-color)] rounded-lg overflow-hidden">
      {/* Header de seccion */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className={iconColor}>{icon}</span>
          <span className="font-medium text-[var(--text-primary)]">{titulo}</span>
          <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--bg-card)] text-[var(--text-muted)]">
            {archivos.length} archivo{archivos.length !== 1 ? 's' : ''}
          </span>
        </div>
        <ChevronRight className={`w-4 h-4 text-[var(--text-muted)] transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {/* Contenido expandible */}
      {expanded && (
        <div className="p-4 space-y-4">
          <p className="text-sm text-[var(--text-muted)]">{descripcion}</p>

          {/* Lista de archivos */}
          {archivos.length > 0 ? (
            <div className="space-y-2">
              {archivos.map((archivo) => (
                <div
                  key={archivo.id}
                  className="flex items-center gap-3 p-3 bg-[var(--bg-tertiary)] rounded-lg hover:bg-[var(--bg-hover)] cursor-pointer group"
                  onClick={() => archivo.tipo_archivo === 'pdf' && onViewPDF(archivo.url, archivo.nombre_original)}
                >
                  <FileText className="w-5 h-5 text-red-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-[var(--text-primary)] truncate">
                      {archivo.nombre_original}
                    </p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {filesService.formatFileSize(archivo.tamano_bytes)}
                      {archivo.descripcion && ` • ${archivo.descripcion}`}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(archivo.id);
                    }}
                    className="p-2 text-red-400 hover:bg-red-500/20 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Eliminar archivo"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-4 text-[var(--text-muted)] text-sm border-2 border-dashed border-[var(--border-color)] rounded-lg">
              No hay archivos. Sube el primero.
            </div>
          )}

          {/* Uploader */}
          <FileUploader
            targetId={unidadId}
            targetType="unidad"
            onUploadSuccess={onUploadSuccess}
          />
        </div>
      )}
    </div>
  );
}

interface UnidadFormProps {
  materiaCode: string;
  onSave: (data: UnidadCreate) => Promise<void>;
  onCancel: () => void;
  initialData?: Partial<UnidadCreate>;
}

function UnidadForm({ materiaCode, onSave, onCancel, initialData }: UnidadFormProps) {
  const [formData, setFormData] = useState<UnidadCreate>({
    materia_code: materiaCode,
    numero: initialData?.numero || 1,
    titulo: initialData?.titulo || '',
    descripcion: initialData?.descripcion || '',
    objetivos_aprendizaje: initialData?.objetivos_aprendizaje || [],
    tiempo_teoria_min: initialData?.tiempo_teoria_min || 60,
    tiempo_practica_min: initialData?.tiempo_practica_min || 120,
  });
  const [nuevoObjetivo, setNuevoObjetivo] = useState('');
  const [saving, setSaving] = useState(false);

  const handleAddObjetivo = () => {
    if (nuevoObjetivo.trim()) {
      setFormData({
        ...formData,
        objetivos_aprendizaje: [...formData.objetivos_aprendizaje!, nuevoObjetivo.trim()]
      });
      setNuevoObjetivo('');
    }
  };

  const handleRemoveObjetivo = (index: number) => {
    setFormData({
      ...formData,
      objetivos_aprendizaje: formData.objetivos_aprendizaje!.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!materiaCode || materiaCode.trim() === '') {
      if (import.meta.env.DEV) console.error('Error: No hay materia seleccionada');
      return;
    }
    setSaving(true);
    try {
      await onSave(formData);
    } finally {
      setSaving(false);
    }
  };

  const inputClass = "w-full p-2 border border-[var(--border-color)] rounded bg-[var(--bg-tertiary)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)]";
  const labelClass = "block text-sm font-medium text-[var(--text-secondary)] mb-1";

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)]">
      <h3 className="text-lg font-semibold text-[var(--text-primary)]">
        {initialData ? 'Editar Unidad' : 'Nueva Unidad'}
      </h3>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Numero de Unidad</label>
          <input
            type="number"
            min="1"
            value={formData.numero}
            onChange={(e) => setFormData({ ...formData, numero: parseInt(e.target.value, 10) })}
            className={inputClass}
            required
          />
        </div>
        <div>
          <label className={labelClass}>Titulo</label>
          <input
            type="text"
            value={formData.titulo}
            onChange={(e) => setFormData({ ...formData, titulo: e.target.value })}
            className={inputClass}
            placeholder="Ej: Variables y Tipos de Datos"
            required
          />
        </div>
      </div>

      <div>
        <label className={labelClass}>Descripcion</label>
        <textarea
          value={formData.descripcion}
          onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
          className={`${inputClass} h-20`}
          placeholder="Descripcion de la unidad..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>
            <Clock className="inline w-4 h-4 mr-1" />
            Tiempo Teoria (min)
          </label>
          <input
            type="number"
            min="0"
            value={formData.tiempo_teoria_min}
            onChange={(e) => setFormData({ ...formData, tiempo_teoria_min: parseInt(e.target.value, 10) })}
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>
            <Code className="inline w-4 h-4 mr-1" />
            Tiempo Practica (min)
          </label>
          <input
            type="number"
            min="0"
            value={formData.tiempo_practica_min}
            onChange={(e) => setFormData({ ...formData, tiempo_practica_min: parseInt(e.target.value, 10) })}
            className={inputClass}
          />
        </div>
      </div>

      <div>
        <label className={labelClass}>
          <Target className="inline w-4 h-4 mr-1" />
          Objetivos de Aprendizaje
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={nuevoObjetivo}
            onChange={(e) => setNuevoObjetivo(e.target.value)}
            className={`flex-1 ${inputClass}`}
            placeholder="Agregar objetivo..."
            onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddObjetivo())}
          />
          <button
            type="button"
            onClick={handleAddObjetivo}
            className="px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
        <ul className="space-y-1">
          {formData.objetivos_aprendizaje?.map((obj, idx) => (
            <li key={idx} className="flex items-center gap-2 p-2 bg-[var(--bg-tertiary)] rounded">
              <span className="flex-1 text-sm text-[var(--text-primary)]">{obj}</span>
              <button
                type="button"
                onClick={() => handleRemoveObjetivo(idx)}
                className="text-red-400 hover:text-red-300"
              >
                <X className="w-4 h-4" />
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t border-[var(--border-color)]">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-[var(--border-color)] rounded text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
        >
          Cancelar
        </button>
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
        >
          {saving ? 'Guardando...' : 'Guardar'}
        </button>
      </div>
    </form>
  );
}

// ==================== Componente Principal ====================

export default function ContentManagementPage() {
  // Estado
  const [materias, setMaterias] = useState<MateriaConUnidades[]>([]);
  const [selectedMateria, setSelectedMateria] = useState<string | null>(null);
  const [selectedUnidad, setSelectedUnidad] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Formularios
  const [showUnidadForm, setShowUnidadForm] = useState(false);
  const [editingUnidad, setEditingUnidad] = useState<UnidadConEjercicios | null>(null);

  // Archivos adjuntos - separados por tipo
  const [archivosTeoricos, setArchivosTeoricos] = useState<ArchivoAdjunto[]>([]);
  const [archivosPracticos, setArchivosPracticos] = useState<ArchivoAdjunto[]>([]);
  const [selectedPDF, setSelectedPDF] = useState<{ url: string; nombre: string } | null>(null);

  // Cargar materias
  const loadMaterias = useCallback(async () => {
    try {
      setLoading(true);
      const data = await academicService.getMaterias({
        solo_activas: false,
        incluir_unidades: true
      });
      // FIX: Ensure data is always an array
      const materiasArray = Array.isArray(data) ? data : (data as unknown as { data: MateriaConUnidades[] })?.data || [];
      setMaterias(materiasArray);
    } catch (err) {
      setError('Error cargando materias');
      if (import.meta.env.DEV) console.error('Error loading materias:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMaterias();
  }, [loadMaterias]);

  // Cargar archivos cuando se selecciona una unidad
  useEffect(() => {
    if (selectedUnidad) {
      filesService.getByUnidad(selectedUnidad)
        .then((archivos) => {
          // Clasificar archivos por descripcion o nombre
          // Los archivos con "teoria" o "teorico" van a teoricos
          // Los archivos con "practica" o "ejercicio" van a practicos
          // El resto va a teoricos por defecto
          const teoricos: ArchivoAdjunto[] = [];
          const practicos: ArchivoAdjunto[] = [];

          archivos.forEach((archivo) => {
            const desc = (archivo.descripcion || '').toLowerCase();
            const nombre = archivo.nombre_original.toLowerCase();

            if (desc.includes('practi') || desc.includes('ejerci') ||
                nombre.includes('practi') || nombre.includes('ejerci') ||
                nombre.includes('taller') || nombre.includes('guia_practica')) {
              practicos.push(archivo);
            } else {
              teoricos.push(archivo);
            }
          });

          setArchivosTeoricos(teoricos);
          setArchivosPracticos(practicos);
        })
        .catch(() => {
          setArchivosTeoricos([]);
          setArchivosPracticos([]);
        });
    } else {
      setArchivosTeoricos([]);
      setArchivosPracticos([]);
    }
  }, [selectedUnidad]);

  // Handlers
  const handleCreateUnidad = async (data: UnidadCreate) => {
    try {
      await academicService.createUnidad(data);
      await loadMaterias();
      setShowUnidadForm(false);
    } catch (err) {
      if (import.meta.env.DEV) console.error('Error creating unidad:', err);
      setError('Error al crear la unidad');
    }
  };

  const handleUpdateUnidad = async (data: UnidadCreate) => {
    if (!editingUnidad) return;
    try {
      await academicService.updateUnidad(editingUnidad.id, {
        titulo: data.titulo,
        descripcion: data.descripcion,
        objetivos_aprendizaje: data.objetivos_aprendizaje,
        tiempo_teoria_min: data.tiempo_teoria_min,
        tiempo_practica_min: data.tiempo_practica_min,
      });
      await loadMaterias();
      setEditingUnidad(null);
    } catch (err) {
      if (import.meta.env.DEV) console.error('Error updating unidad:', err);
      setError('Error al actualizar la unidad');
    }
  };

  const handlePublicarUnidad = async (unidadId: string) => {
    try {
      await academicService.publicarUnidad(unidadId);
      await loadMaterias();
    } catch (err) {
      if (import.meta.env.DEV) console.error('Error publishing unidad:', err);
      setError('Error al publicar la unidad');
    }
  };

  const handleDeleteUnidad = async (unidadId: string) => {
    if (confirm('Eliminar esta unidad y todo su contenido?')) {
      try {
        await academicService.deleteUnidad(unidadId);
        if (selectedUnidad === unidadId) {
          setSelectedUnidad(null);
        }
        await loadMaterias();
      } catch (err) {
        if (import.meta.env.DEV) console.error('Error deleting unidad:', err);
        setError('Error al eliminar la unidad');
      }
    }
  };

  const handleDeleteArchivo = async (archivoId: string, tipo: 'teoria' | 'practica') => {
    try {
      await filesService.deleteFile(archivoId);
      if (tipo === 'teoria') {
        setArchivosTeoricos(prev => prev.filter(a => a.id !== archivoId));
      } else {
        setArchivosPracticos(prev => prev.filter(a => a.id !== archivoId));
      }
    } catch (err) {
      if (import.meta.env.DEV) console.error('Error deleting file:', err);
      setError('Error al eliminar el archivo');
    }
  };

  const handleUploadSuccess = (archivo: { id: string; nombre: string; url: string }, tipo: 'teoria' | 'practica') => {
    const newArchivo: ArchivoAdjunto = {
      id: archivo.id,
      nombre_original: archivo.nombre,
      tipo_archivo: 'pdf',
      tamano_bytes: 0,
      descripcion: tipo === 'teoria' ? 'Material Teorico' : 'Material Practico',
      orden: (tipo === 'teoria' ? archivosTeoricos.length : archivosPracticos.length) + 1,
      url: archivo.url,
    };

    if (tipo === 'teoria') {
      setArchivosTeoricos(prev => [...prev, newArchivo]);
    } else {
      setArchivosPracticos(prev => [...prev, newArchivo]);
    }
  };

  // Datos derivados
  const materiaActual = materias.find(m => m.code === selectedMateria);
  const unidades: UnidadConEjercicios[] = materiaActual?.unidades || [];
  const unidadActual = unidades.find(u => u.id === selectedUnidad);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2 text-[var(--text-primary)]">
            <Book className="w-7 h-7 text-indigo-500" />
            Gestion de Contenido Academico
          </h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Organiza el contenido teorico y practico de tus materias
          </p>
        </div>
        <button
          onClick={loadMaterias}
          className="p-2 text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] rounded-lg transition-colors"
          title="Recargar"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Breadcrumb de navegacion */}
      <Breadcrumb
        materia={materiaActual}
        unidad={unidadActual}
        onClickMateria={() => {
          setSelectedMateria(null);
          setSelectedUnidad(null);
        }}
        onClickUnidad={() => setSelectedUnidad(null)}
      />

      {error && (
        <div className="mb-4 p-3 bg-red-500/20 text-red-400 rounded-lg border border-red-500/30 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="p-1 hover:bg-red-500/20 rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Panel Izquierdo: Lista de Materias */}
        <div className="col-span-3 bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)] p-4">
          <h2 className="font-semibold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
            <Book className="w-5 h-5 text-indigo-400" />
            Materias ({materias.length})
          </h2>
          {materias.length === 0 ? (
            <p className="text-[var(--text-muted)] text-center py-8 text-sm">
              No hay materias disponibles.
              <br />
              Crea una desde "Gestion de Materias".
            </p>
          ) : (
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {materias.map((materia) => (
                <button
                  key={materia.code}
                  onClick={() => {
                    setSelectedMateria(materia.code);
                    setSelectedUnidad(null);
                  }}
                  className={`w-full text-left p-3 rounded-lg transition ${
                    selectedMateria === materia.code
                      ? 'bg-indigo-500/20 border-indigo-500/50 border'
                      : 'hover:bg-[var(--bg-hover)] border border-transparent'
                  }`}
                >
                  <div className="font-medium text-[var(--text-primary)]">{materia.name}</div>
                  <div className="text-sm text-[var(--text-secondary)] flex items-center gap-2">
                    <span>{materia.unidades?.length || 0} unidades</span>
                    <span className="text-[var(--text-muted)]">•</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${
                      materia.language === 'python' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-orange-500/20 text-orange-400'
                    }`}>
                      {materia.language}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Panel Central: Unidades */}
        <div className="col-span-4 bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)] p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-semibold flex items-center gap-2 text-[var(--text-primary)]">
              <ChevronRight className="w-5 h-5 text-indigo-400" />
              Unidades {materiaActual ? `de ${materiaActual.code}` : ''}
            </h2>
            {selectedMateria && (
              <button
                onClick={() => setShowUnidadForm(true)}
                className="p-2 text-indigo-400 hover:bg-indigo-500/20 rounded"
                title="Crear nueva unidad"
              >
                <Plus className="w-5 h-5" />
              </button>
            )}
          </div>

          {(showUnidadForm || editingUnidad) && selectedMateria && (
            <div className="mb-4">
              <UnidadForm
                materiaCode={selectedMateria}
                onSave={editingUnidad ? handleUpdateUnidad : handleCreateUnidad}
                onCancel={() => {
                  setShowUnidadForm(false);
                  setEditingUnidad(null);
                }}
                initialData={editingUnidad ? {
                  numero: editingUnidad.numero,
                  titulo: editingUnidad.titulo,
                  descripcion: editingUnidad.descripcion || '',
                  objetivos_aprendizaje: editingUnidad.objetivos_aprendizaje || [],
                  tiempo_teoria_min: editingUnidad.tiempo_teoria_min,
                  tiempo_practica_min: editingUnidad.tiempo_practica_min,
                } : undefined}
              />
            </div>
          )}

          {/* Ocultar lista de unidades mientras se edita o crea */}
          {!selectedMateria ? (
            <div className="text-center py-12">
              <Book className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3 opacity-50" />
              <p className="text-[var(--text-muted)]">
                Selecciona una materia para ver sus unidades
              </p>
            </div>
          ) : (showUnidadForm || editingUnidad) ? (
            null /* Lista oculta mientras se edita/crea */
          ) : unidades.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3 opacity-50" />
              <p className="text-[var(--text-muted)]">No hay unidades.</p>
              <button
                onClick={() => setShowUnidadForm(true)}
                className="mt-2 text-indigo-400 hover:underline text-sm"
              >
                Crear la primera unidad
              </button>
            </div>
          ) : (
            <div className="space-y-2 max-h-[55vh] overflow-y-auto">
              {unidades.map((unidad) => (
                <div
                  key={unidad.id}
                  onClick={() => setSelectedUnidad(unidad.id)}
                  className={`p-3 rounded-lg cursor-pointer transition ${
                    selectedUnidad === unidad.id
                      ? 'bg-indigo-500/20 border-indigo-500/50 border'
                      : 'hover:bg-[var(--bg-hover)] border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-medium text-[var(--text-primary)]">
                      Unidad {unidad.numero}: {unidad.titulo}
                    </div>
                    <div className="flex items-center gap-1">
                      {unidad.esta_publicada ? (
                        <span title="Publicada"><Eye className="w-4 h-4 text-green-400" /></span>
                      ) : (
                        <span title="Borrador"><EyeOff className="w-4 h-4 text-[var(--text-muted)]" /></span>
                      )}
                    </div>
                  </div>
                  <div className="text-sm text-[var(--text-secondary)] mt-1 flex items-center gap-2">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {unidad.tiempo_teoria_min}m teoria
                    </span>
                    <span className="text-[var(--text-muted)]">+</span>
                    <span className="flex items-center gap-1">
                      <Code className="w-3 h-3" />
                      {unidad.tiempo_practica_min}m practica
                    </span>
                  </div>
                  <div className="flex gap-2 mt-2">
                    {!unidad.esta_publicada && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handlePublicarUnidad(unidad.id);
                        }}
                        className="text-xs px-2 py-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30"
                      >
                        Publicar
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setEditingUnidad(unidad);
                        setShowUnidadForm(false);
                      }}
                      className="text-xs px-2 py-1 bg-indigo-500/20 text-indigo-400 rounded hover:bg-indigo-500/30 flex items-center gap-1"
                    >
                      <Edit2 className="w-3 h-3" />
                      Editar
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteUnidad(unidad.id);
                      }}
                      className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30"
                    >
                      Eliminar
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Panel Derecho: Contenido de Unidad */}
        <div className="col-span-5 bg-[var(--bg-card)] rounded-lg border border-[var(--border-color)] p-4">
          <h2 className="font-semibold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
            <FileText className="w-5 h-5 text-indigo-400" />
            Contenido de la Unidad
          </h2>

          {!selectedUnidad ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-3 opacity-50" />
              <p className="text-[var(--text-muted)]">
                Selecciona una unidad para gestionar su contenido
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Info de la unidad seleccionada */}
              {unidadActual && (
                <div className="p-3 bg-indigo-500/10 border border-indigo-500/30 rounded-lg">
                  <p className="text-sm text-[var(--text-primary)] font-medium">
                    {unidadActual.titulo}
                  </p>
                  {unidadActual.descripcion && (
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      {unidadActual.descripcion}
                    </p>
                  )}
                  {unidadActual.objetivos_aprendizaje && unidadActual.objetivos_aprendizaje.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-[var(--text-muted)] mb-1">Objetivos:</p>
                      <ul className="text-xs text-[var(--text-secondary)] list-disc list-inside">
                        {unidadActual.objetivos_aprendizaje.slice(0, 3).map((obj, idx) => (
                          <li key={idx}>{obj}</li>
                        ))}
                        {unidadActual.objetivos_aprendizaje.length > 3 && (
                          <li className="text-[var(--text-muted)]">
                            +{unidadActual.objetivos_aprendizaje.length - 3} mas...
                          </li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Seccion Material Teorico */}
              <ArchivosSection
                titulo="Material Teorico"
                descripcion="PDFs con contenido teorico: apuntes, presentaciones, lecturas."
                icon={<BookOpen className="w-5 h-5" />}
                iconColor="text-blue-400"
                archivos={archivosTeoricos}
                unidadId={selectedUnidad}
                tipoPrefix="teoria"
                onViewPDF={(url, nombre) => setSelectedPDF({ url, nombre })}
                onDelete={(id) => handleDeleteArchivo(id, 'teoria')}
                onUploadSuccess={(archivo) => handleUploadSuccess(archivo, 'teoria')}
              />

              {/* Seccion Material Practico */}
              <ArchivosSection
                titulo="Material Practico"
                descripcion="PDFs con ejercicios, talleres, guias practicas y actividades."
                icon={<Wrench className="w-5 h-5" />}
                iconColor="text-orange-400"
                archivos={archivosPracticos}
                unidadId={selectedUnidad}
                tipoPrefix="practica"
                onViewPDF={(url, nombre) => setSelectedPDF({ url, nombre })}
                onDelete={(id) => handleDeleteArchivo(id, 'practica')}
                onUploadSuccess={(archivo) => handleUploadSuccess(archivo, 'practica')}
              />
            </div>
          )}
        </div>
      </div>

      {/* Modal de PDF */}
      {selectedPDF && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
          <div className="bg-[var(--bg-card)] rounded-lg w-full max-w-4xl mx-4 border border-[var(--border-color)]">
            <PDFViewer
              url={selectedPDF.url}
              filename={selectedPDF.nombre}
              onClose={() => setSelectedPDF(null)}
              height="70vh"
            />
          </div>
        </div>
      )}
    </div>
  );
}
