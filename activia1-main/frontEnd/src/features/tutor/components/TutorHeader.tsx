/**
 * TutorHeader Component - Header with title and action buttons
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

import {
  Brain,
  Loader2,
  GitBranch,
  Shield,
  Plus,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react';

interface TutorHeaderProps {
  // Traceability
  lastTraceId: string | null;
  isLoadingTraceability: boolean;
  onAnalyzeTraceability: () => void;

  // Risk analysis
  hasSession: boolean;
  isLoadingRisks: boolean;
  onAnalyzeRisks: () => void;

  // Session
  onNewSession: () => void;

  // Panel visibility
  showRiskPanel: boolean;
  onToggleRiskPanel: () => void;
}

export function TutorHeader({
  lastTraceId,
  isLoadingTraceability,
  onAnalyzeTraceability,
  hasSession,
  isLoadingRisks,
  onAnalyzeRisks,
  onNewSession,
  showRiskPanel,
  onToggleRiskPanel,
}: TutorHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Brain className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Tutor IA</h1>
          <p className="text-sm text-[var(--text-secondary)]">
            Aprende con guía cognitiva personalizada
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onAnalyzeTraceability}
          disabled={!lastTraceId || isLoadingTraceability}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-primary)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          title="Ver trazabilidad N4 de la última interacción"
        >
          {isLoadingTraceability ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <GitBranch className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">
            {isLoadingTraceability ? 'Cargando...' : 'Trazabilidad'}
          </span>
        </button>

        <button
          onClick={onAnalyzeRisks}
          disabled={!hasSession || isLoadingRisks}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-primary)] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          title="Ver análisis detallado de riesgos 5D"
        >
          {isLoadingRisks ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Shield className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">
            {isLoadingRisks ? 'Analizando...' : 'Ver Reporte'}
          </span>
        </button>

        <button
          onClick={onNewSession}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-primary)] transition-all"
        >
          <Plus className="w-4 h-4" />
          <span className="hidden sm:inline">Nueva Sesión</span>
        </button>

        <button
          onClick={onToggleRiskPanel}
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-primary)] transition-all"
          title={showRiskPanel ? 'Ocultar panel de riesgos' : 'Mostrar panel de riesgos'}
        >
          {showRiskPanel ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </div>
  );
}
