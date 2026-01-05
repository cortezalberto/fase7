/**
 * CognitiveTimeline - Visual timeline of student's cognitive journey
 *
 * Cortez82: Created for Mejora 4.4 - Timeline visual del camino cognitivo
 *
 * Displays:
 * - Cognitive state transitions over time
 * - Risk indicators at critical points
 * - AI involvement levels
 * - Tutor interventions
 */

import { useMemo } from 'react';
import {
  Brain,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus,
  Bot,
  Lightbulb,
  XCircle,
  RefreshCw,
} from 'lucide-react';

// Types for the cognitive timeline
interface CognitivePathEntry {
  state: string;
  timestamp: string;
  duration_seconds?: number;
  ai_involvement?: number;
}

interface Transition {
  from_state: string;
  to_state: string;
  timestamp: string;
  is_regression?: boolean;
}

interface CognitiveTimelineProps {
  cognitivePath: CognitivePathEntry[];
  transitions: Transition[];
  timeInStates: Record<string, number>;
  insights?: string[];
  risks?: Array<{
    type: string;
    level: string;
    timestamp?: string;
  }>;
}

// State configurations
const STATE_CONFIG: Record<string, {
  icon: typeof Brain;
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
  description: string;
}> = {
  INICIO: {
    icon: Clock,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    borderColor: 'border-blue-500/50',
    label: 'Inicio',
    description: 'Comenzando la actividad',
  },
  EXPLORACION: {
    icon: Lightbulb,
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    borderColor: 'border-yellow-500/50',
    label: 'Exploración',
    description: 'Investigando el problema',
  },
  IMPLEMENTACION: {
    icon: TrendingUp,
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    borderColor: 'border-green-500/50',
    label: 'Implementación',
    description: 'Escribiendo código',
  },
  DEPURACION: {
    icon: RefreshCw,
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    borderColor: 'border-orange-500/50',
    label: 'Depuración',
    description: 'Corrigiendo errores',
  },
  CAMBIO_ESTRATEGIA: {
    icon: RefreshCw,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    borderColor: 'border-purple-500/50',
    label: 'Cambio de Estrategia',
    description: 'Replanteando el enfoque',
  },
  VALIDACION: {
    icon: CheckCircle,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
    borderColor: 'border-emerald-500/50',
    label: 'Validación',
    description: 'Verificando la solución',
  },
  ESTANCAMIENTO: {
    icon: XCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    borderColor: 'border-red-500/50',
    label: 'Estancamiento',
    description: 'Bloqueado, necesita ayuda',
  },
  REFLEXION: {
    icon: Brain,
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/20',
    borderColor: 'border-indigo-500/50',
    label: 'Reflexión',
    description: 'Analizando el proceso',
  },
};

const DEFAULT_STATE_CONFIG = {
  icon: Brain,
  color: 'text-gray-400',
  bgColor: 'bg-gray-500/20',
  borderColor: 'border-gray-500/50',
  label: 'Desconocido',
  description: 'Estado no identificado',
};

function getStateConfig(state: string) {
  return STATE_CONFIG[state] || DEFAULT_STATE_CONFIG;
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h ${Math.round((seconds % 3600) / 60)}m`;
}

function formatTimestamp(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return timestamp;
  }
}

export function CognitiveTimeline({
  cognitivePath,
  transitions,
  timeInStates,
  insights = [],
  risks = [],
}: CognitiveTimelineProps) {
  // Calculate summary statistics
  const summary = useMemo(() => {
    const totalTime = Object.values(timeInStates).reduce((a, b) => a + b, 0);
    const stagnationTime = timeInStates['ESTANCAMIENTO'] || 0;
    const productiveTime = totalTime - stagnationTime;
    const regressionCount = transitions.filter(t => t.is_regression).length;

    // Calculate average AI involvement
    const aiValues = cognitivePath
      .map(p => p.ai_involvement)
      .filter((v): v is number => v !== undefined);
    const avgAI = aiValues.length > 0
      ? aiValues.reduce((a, b) => a + b, 0) / aiValues.length
      : 0;

    return {
      totalTime,
      productiveTime,
      stagnationTime,
      stagnationPercent: totalTime > 0 ? (stagnationTime / totalTime) * 100 : 0,
      regressionCount,
      avgAI,
      totalTransitions: transitions.length,
      uniqueStates: new Set(cognitivePath.map(p => p.state)).size,
    };
  }, [cognitivePath, transitions, timeInStates]);

  // Get AI dependency color
  const getAIDependencyColor = (value: number) => {
    if (value > 0.7) return 'text-red-400';
    if (value > 0.4) return 'text-yellow-400';
    return 'text-green-400';
  };

  // Get AI dependency icon
  const getAIDependencyIcon = (value: number) => {
    if (value > 0.7) return TrendingUp;
    if (value > 0.4) return Minus;
    return TrendingDown;
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Clock className="w-4 h-4" />
            Tiempo Total
          </div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">
            {formatDuration(summary.totalTime)}
          </div>
        </div>

        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Brain className="w-4 h-4" />
            Estados Visitados
          </div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">
            {summary.uniqueStates}
          </div>
        </div>

        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Bot className="w-4 h-4" />
            Dependencia IA
          </div>
          <div className={`text-2xl font-bold ${getAIDependencyColor(summary.avgAI)}`}>
            {Math.round(summary.avgAI * 100)}%
          </div>
        </div>

        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <AlertTriangle className="w-4 h-4" />
            Estancamiento
          </div>
          <div className={`text-2xl font-bold ${summary.stagnationPercent > 30 ? 'text-red-400' : 'text-green-400'}`}>
            {Math.round(summary.stagnationPercent)}%
          </div>
        </div>
      </div>

      {/* Time Distribution Bar */}
      <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Distribución de Tiempo por Estado
        </h3>
        <div className="flex h-8 rounded-lg overflow-hidden">
          {Object.entries(timeInStates).map(([state, time]) => {
            const config = getStateConfig(state);
            const percent = summary.totalTime > 0 ? (time / summary.totalTime) * 100 : 0;
            if (percent < 1) return null;
            return (
              <div
                key={state}
                className={`${config.bgColor} border-r border-[var(--bg-primary)] last:border-r-0 flex items-center justify-center`}
                style={{ width: `${percent}%` }}
                title={`${config.label}: ${formatDuration(time)} (${Math.round(percent)}%)`}
              >
                {percent > 10 && (
                  <span className={`text-xs font-medium ${config.color}`}>
                    {Math.round(percent)}%
                  </span>
                )}
              </div>
            );
          })}
        </div>
        <div className="flex flex-wrap gap-3 mt-3">
          {Object.entries(timeInStates).map(([state, time]) => {
            const config = getStateConfig(state);
            return (
              <div key={state} className="flex items-center gap-1.5 text-xs">
                <div className={`w-3 h-3 rounded ${config.bgColor} ${config.borderColor} border`} />
                <span className="text-[var(--text-muted)]">{config.label}</span>
                <span className="text-[var(--text-secondary)]">{formatDuration(time)}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-4">
          Camino Cognitivo
        </h3>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-[var(--border-color)]" />

          {/* Timeline entries */}
          <div className="space-y-4">
            {cognitivePath.slice(-20).map((entry, index) => {
              const config = getStateConfig(entry.state);
              const Icon = config.icon;
              const AIIcon = entry.ai_involvement !== undefined
                ? getAIDependencyIcon(entry.ai_involvement)
                : null;

              // Check if there's a risk at this point
              const hasRisk = risks.some(r =>
                r.timestamp && new Date(r.timestamp).getTime() === new Date(entry.timestamp).getTime()
              );

              return (
                <div key={`${entry.timestamp}-${index}`} className="relative flex gap-4">
                  {/* Timeline node */}
                  <div
                    className={`
                      relative z-10 w-12 h-12 rounded-full flex items-center justify-center
                      ${config.bgColor} ${config.borderColor} border-2
                      ${hasRisk ? 'ring-2 ring-red-500 ring-offset-2 ring-offset-[var(--bg-tertiary)]' : ''}
                    `}
                  >
                    <Icon className={`w-5 h-5 ${config.color}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 pb-4">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-medium ${config.color}`}>
                        {config.label}
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">
                        {formatTimestamp(entry.timestamp)}
                      </span>
                      {entry.duration_seconds !== undefined && (
                        <span className="text-xs bg-[var(--bg-secondary)] px-2 py-0.5 rounded text-[var(--text-muted)]">
                          {formatDuration(entry.duration_seconds)}
                        </span>
                      )}
                    </div>

                    <p className="text-sm text-[var(--text-muted)]">
                      {config.description}
                    </p>

                    {/* AI Involvement indicator */}
                    {entry.ai_involvement !== undefined && AIIcon && (
                      <div className="flex items-center gap-1 mt-2">
                        <Bot className="w-3 h-3 text-[var(--text-muted)]" />
                        <div className="flex items-center gap-1">
                          <div className="w-24 h-1.5 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                entry.ai_involvement > 0.7 ? 'bg-red-500' :
                                entry.ai_involvement > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                              }`}
                              style={{ width: `${entry.ai_involvement * 100}%` }}
                            />
                          </div>
                          <span className={`text-xs ${getAIDependencyColor(entry.ai_involvement)}`}>
                            {Math.round(entry.ai_involvement * 100)}%
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Risk indicator */}
                    {hasRisk && (
                      <div className="flex items-center gap-1 mt-2 text-red-400">
                        <AlertTriangle className="w-3 h-3" />
                        <span className="text-xs">Riesgo detectado</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {cognitivePath.length > 20 && (
          <p className="text-xs text-[var(--text-muted)] mt-4 text-center">
            Mostrando los últimos 20 estados de {cognitivePath.length} totales
          </p>
        )}
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4 text-yellow-400" />
            Insights del Proceso
          </h3>
          <ul className="space-y-2">
            {insights.map((insight, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm text-[var(--text-muted)]"
              >
                <span className="text-yellow-400 mt-0.5">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Transitions summary */}
      {summary.regressionCount > 0 && (
        <div className="bg-orange-500/10 rounded-lg p-4 border border-orange-500/30">
          <div className="flex items-center gap-2 text-orange-400 mb-2">
            <RefreshCw className="w-4 h-4" />
            <span className="font-medium">Regresiones Detectadas</span>
          </div>
          <p className="text-sm text-[var(--text-muted)]">
            Se detectaron {summary.regressionCount} regresiones (volver a un estado anterior).
            Esto puede indicar dificultades o cambios de estrategia.
          </p>
        </div>
      )}
    </div>
  );
}

export default CognitiveTimeline;
