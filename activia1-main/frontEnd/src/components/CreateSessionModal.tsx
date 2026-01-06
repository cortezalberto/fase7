// Cortez93: Migrated to React 19 useActionState for cleaner form state management
import { useState, useActionState } from 'react';
import { Plus } from 'lucide-react';
// MIGRATED: Using new sessionsService instead of legacy api
import { sessionsService } from '../services/api';
import { SessionMode } from '../types/api.types';
import type { SessionCreate } from '../types/api.types';
// FE-CODE-003: Use shared Modal component
import { Modal } from '../shared/components/Modal';

interface CreateSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSessionCreated: (sessionId: string) => void;
}

// Cortez93: Form state type for useActionState
interface CreateSessionFormState {
  error: string | null;
  success: boolean;
}

// FE-REACT-001: Use function component pattern instead of React.FC (deprecated in React 19)
function CreateSessionModal({ isOpen, onClose, onSessionCreated }: CreateSessionModalProps) {
  const [formData, setFormData] = useState<SessionCreate>({
    student_id: '',
    activity_id: '',
    mode: SessionMode.TUTOR,
    simulator_type: undefined,
  });

  // Cortez93: React 19 useActionState for form submission
  // Replaces manual isCreating/error state management
  const [formState, submitAction, isPending] = useActionState<CreateSessionFormState, FormData>(
    async (_prevState, _formData): Promise<CreateSessionFormState> => {
      // Validar que se seleccione simulator_type cuando mode es SIMULATOR
      if (formData.mode === SessionMode.SIMULATOR && !formData.simulator_type) {
        return { error: 'Debe seleccionar un tipo de simulador para el modo Simulador Profesional', success: false };
      }

      try {
        // MIGRATED: Using sessionsService.create() instead of api.createSession()
        const session = await sessionsService.create({
          student_id: formData.student_id,
          activity_id: formData.activity_id,
          mode: formData.mode,
          simulator_type: formData.simulator_type,
        });
        onSessionCreated(session.id);
        onClose();
        // Reset form
        setFormData({
          student_id: '',
          activity_id: '',
          mode: SessionMode.TUTOR,
          simulator_type: undefined,
        });
        return { error: null, success: true };
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Error al crear la sesión';
        return { error: errorMessage, success: false };
      }
    },
    { error: null, success: false }
  );

  // FE-CODE-003: Use shared Modal component for consistent behavior
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Nueva Sesión"
      icon={<Plus className="w-6 h-6 text-purple-400" />}
    >
      {/* Cortez93: Use action prop with submitAction from useActionState */}
      <form action={submitAction} className="space-y-4">
        {/* Student ID */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            ID del Estudiante
          </label>
          <input
            type="text"
            value={formData.student_id}
            onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
            className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
            placeholder="student_001"
            required
          />
        </div>

        {/* Activity ID */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            ID de la Actividad
          </label>
          <input
            type="text"
            value={formData.activity_id}
            onChange={(e) => setFormData({ ...formData, activity_id: e.target.value })}
            className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
            placeholder="prog2_tp1_colas"
            required
          />
        </div>

        {/* Mode */}
        <div>
          <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
            Modo de Sesión
          </label>
          <select
            value={formData.mode}
            onChange={(e) => setFormData({ ...formData, mode: e.target.value as SessionMode })}
            className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
          >
            <option value="TUTOR">Tutor Socrático</option>
            <option value="SIMULATOR">Simulador Profesional</option>
            <option value="PRACTICE">Práctica Libre</option>
            <option value="EVALUATOR">Evaluación de Proceso</option>
            <option value="RISK_ANALYST">Análisis de Riesgos</option>
            <option value="GOVERNANCE">Gobernanza</option>
          </select>
        </div>

        {/* Simulator Type (conditional) */}
        {formData.mode === SessionMode.SIMULATOR && (
          <div>
            <label className="block text-sm font-medium text-[var(--text-secondary)] mb-2">
              Tipo de Simulador
            </label>
            <select
              value={formData.simulator_type || ''}
              onChange={(e) => setFormData({ ...formData, simulator_type: e.target.value })}
              className="w-full px-4 py-3 bg-[var(--bg-tertiary)] border border-[var(--border-color)] rounded-lg text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-primary)]"
            >
              <option value="">Seleccionar...</option>
              <option value="product_owner">Product Owner</option>
              <option value="scrum_master">Scrum Master</option>
              <option value="tech_interviewer">Tech Interviewer</option>
              <option value="incident_responder">Incident Responder</option>
              <option value="client">Cliente</option>
              <option value="devsecops">DevSecOps</option>
            </select>
          </div>
        )}

        {/* Cortez93: Use formState.error from useActionState */}
        {formState.error && (
          <div className="bg-[var(--error)]/10 border border-[var(--error)]/30 rounded-lg p-3 text-[var(--error)] text-sm">
            {formState.error}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-[var(--bg-tertiary)] text-[var(--text-secondary)] rounded-lg font-medium hover:bg-[var(--bg-hover)] transition-colors"
          >
            Cancelar
          </button>
          {/* Cortez93: Use isPending from useActionState instead of manual isCreating */}
          <button
            type="submit"
            disabled={isPending}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? 'Creando...' : 'Crear Sesión'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default CreateSessionModal;
