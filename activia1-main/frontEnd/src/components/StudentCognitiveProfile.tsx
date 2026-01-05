/**
 * StudentCognitiveProfile - Student's cognitive process dashboard
 *
 * Cortez82: Created for Mejora 4.7 - Dashboard cognitivo para el estudiante
 *
 * Shows students their own cognitive process metrics:
 * - Time in each cognitive state
 * - AI dependency trends
 * - Improvement indicators
 * - Tips based on patterns
 */

import { useMemo } from 'react';
import {
  Brain,
  TrendingUp,
  TrendingDown,
  Clock,
  Bot,
  Award,
  CheckCircle2,
  Lightbulb,
  Activity,
} from 'lucide-react';

interface SessionMetrics {
  session_id: string;
  date: string;
  duration_minutes: number;
  trace_count: number;
  ai_dependency: number;
  cognitive_states: Record<string, number>;
  risks_detected: number;
}

interface StudentCognitiveProfileProps {
  studentId: string;
  recentSessions: SessionMetrics[];
  overallMetrics?: {
    total_sessions: number;
    total_time_minutes: number;
    avg_ai_dependency: number;
    most_common_state: string;
    improvement_score: number; // -1 to 1, positive = improving
  };
}

// Tips based on patterns
const TIPS: Record<string, string[]> = {
  high_ai: [
    'Intenta resolver el siguiente paso por tu cuenta antes de pedir ayuda.',
    'Escribe primero tu idea en pseudocodigo antes de preguntar al tutor.',
    'Cuando recibas una sugerencia, explicala con tus propias palabras.',
  ],
  stagnation: [
    'Divide el problema en partes mas pequenas.',
    'Revisa conceptos basicos relacionados con el tema.',
    'Intenta explicar el problema a alguien (o a ti mismo en voz alta).',
  ],
  good_progress: [
    'Excelente trabajo manteniendo un buen ritmo.',
    'Tu autonomia esta mejorando, sigue asi.',
    'Considera ayudar a companeros que tengan dificultades.',
  ],
  balanced: [
    'Tu uso de la IA es equilibrado.',
    'Continua reflexionando sobre cada solucion que recibas.',
    'Documenta tus aprendizajes para futuras referencias.',
  ],
};

function getTips(aiDependency: number, stagnationPercent: number, isImproving: boolean): string[] {
  if (aiDependency > 0.7) return TIPS.high_ai;
  if (stagnationPercent > 30) return TIPS.stagnation;
  if (isImproving) return TIPS.good_progress;
  return TIPS.balanced;
}

const STATE_LABELS: Record<string, string> = {
  INICIO: 'Inicio',
  EXPLORACION: 'Exploracion',
  IMPLEMENTACION: 'Implementacion',
  DEPURACION: 'Depuracion',
  CAMBIO_ESTRATEGIA: 'Cambio de Estrategia',
  VALIDACION: 'Validacion',
  ESTANCAMIENTO: 'Estancamiento',
  REFLEXION: 'Reflexion',
};

const STATE_COLORS: Record<string, string> = {
  INICIO: 'bg-blue-500',
  EXPLORACION: 'bg-yellow-500',
  IMPLEMENTACION: 'bg-green-500',
  DEPURACION: 'bg-orange-500',
  CAMBIO_ESTRATEGIA: 'bg-purple-500',
  VALIDACION: 'bg-emerald-500',
  ESTANCAMIENTO: 'bg-red-500',
  REFLEXION: 'bg-indigo-500',
};

function formatMinutes(minutes: number): string {
  if (minutes < 60) return `${Math.round(minutes)}m`;
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function StudentCognitiveProfile({
  studentId: _studentId,  // Reserved for future personalization features
  recentSessions,
  overallMetrics: _overallMetrics,  // Reserved for aggregated metrics display
}: StudentCognitiveProfileProps) {
  // Calculate aggregated metrics from recent sessions
  const metrics = useMemo(() => {
    if (recentSessions.length === 0) {
      return {
        avgAIDependency: 0,
        totalTime: 0,
        stagnationPercent: 0,
        stateDistribution: {} as Record<string, number>,
        trend: 0,
        isImproving: false,
      };
    }

    // Calculate averages
    const avgAI = recentSessions.reduce((sum, s) => sum + s.ai_dependency, 0) / recentSessions.length;
    const totalTime = recentSessions.reduce((sum, s) => sum + s.duration_minutes, 0);

    // Aggregate cognitive states
    const stateDistribution: Record<string, number> = {};
    recentSessions.forEach(session => {
      Object.entries(session.cognitive_states).forEach(([state, count]) => {
        stateDistribution[state] = (stateDistribution[state] || 0) + count;
      });
    });

    const totalStates = Object.values(stateDistribution).reduce((a, b) => a + b, 0);
    const stagnationCount = stateDistribution['ESTANCAMIENTO'] || 0;
    const stagnationPercent = totalStates > 0 ? (stagnationCount / totalStates) * 100 : 0;

    // Calculate trend (compare first half vs second half of sessions)
    const midpoint = Math.floor(recentSessions.length / 2);
    if (midpoint > 0) {
      const firstHalf = recentSessions.slice(0, midpoint);
      const secondHalf = recentSessions.slice(midpoint);
      const firstAvgAI = firstHalf.reduce((sum, s) => sum + s.ai_dependency, 0) / firstHalf.length;
      const secondAvgAI = secondHalf.reduce((sum, s) => sum + s.ai_dependency, 0) / secondHalf.length;
      const trend = firstAvgAI - secondAvgAI; // Positive = improving (less AI dependency)
      return {
        avgAIDependency: avgAI,
        totalTime,
        stagnationPercent,
        stateDistribution,
        trend,
        isImproving: trend > 0.05,
      };
    }

    return {
      avgAIDependency: avgAI,
      totalTime,
      stagnationPercent,
      stateDistribution,
      trend: 0,
      isImproving: false,
    };
  }, [recentSessions]);

  const tips = useMemo(
    () => getTips(metrics.avgAIDependency, metrics.stagnationPercent, metrics.isImproving),
    [metrics.avgAIDependency, metrics.stagnationPercent, metrics.isImproving]
  );

  if (recentSessions.length === 0) {
    return (
      <div className="bg-[var(--bg-tertiary)] rounded-lg p-6 border border-[var(--border-color)]">
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-6 h-6 text-indigo-400" />
          <h2 className="text-lg font-semibold text-[var(--text-primary)]">
            Mi Proceso Cognitivo
          </h2>
        </div>
        <p className="text-[var(--text-muted)] text-center py-8">
          Aun no hay sesiones registradas. Completa algunas actividades para ver tu progreso.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Brain className="w-6 h-6 text-indigo-400" />
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Mi Proceso Cognitivo
        </h2>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Sessions */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Activity className="w-4 h-4" />
            Sesiones
          </div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">
            {recentSessions.length}
          </div>
        </div>

        {/* Total Time */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Clock className="w-4 h-4" />
            Tiempo Total
          </div>
          <div className="text-2xl font-bold text-[var(--text-primary)]">
            {formatMinutes(metrics.totalTime)}
          </div>
        </div>

        {/* AI Dependency */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            <Bot className="w-4 h-4" />
            Uso de IA
          </div>
          <div className={`text-2xl font-bold ${
            metrics.avgAIDependency > 0.7 ? 'text-red-400' :
            metrics.avgAIDependency > 0.4 ? 'text-yellow-400' : 'text-green-400'
          }`}>
            {Math.round(metrics.avgAIDependency * 100)}%
          </div>
        </div>

        {/* Trend */}
        <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
          <div className="flex items-center gap-2 text-[var(--text-muted)] text-sm mb-1">
            {metrics.isImproving ? (
              <TrendingUp className="w-4 h-4 text-green-400" />
            ) : (
              <TrendingDown className="w-4 h-4 text-yellow-400" />
            )}
            Tendencia
          </div>
          <div className={`text-2xl font-bold ${metrics.isImproving ? 'text-green-400' : 'text-yellow-400'}`}>
            {metrics.isImproving ? 'Mejorando' : 'Estable'}
          </div>
        </div>
      </div>

      {/* State Distribution */}
      <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Distribucion de Estados Cognitivos
        </h3>
        <div className="space-y-2">
          {Object.entries(metrics.stateDistribution)
            .sort(([, a], [, b]) => b - a)
            .map(([state, count]) => {
              const total = Object.values(metrics.stateDistribution).reduce((a, b) => a + b, 0);
              const percent = total > 0 ? (count / total) * 100 : 0;
              return (
                <div key={state} className="flex items-center gap-3">
                  <div className="w-32 text-sm text-[var(--text-muted)]">
                    {STATE_LABELS[state] || state}
                  </div>
                  <div className="flex-1 h-4 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                    <div
                      className={`h-full ${STATE_COLORS[state] || 'bg-gray-500'} transition-all duration-500`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                  <div className="w-12 text-sm text-[var(--text-secondary)] text-right">
                    {Math.round(percent)}%
                  </div>
                </div>
              );
            })}
        </div>
      </div>

      {/* AI Dependency History */}
      <div className="bg-[var(--bg-tertiary)] rounded-lg p-4 border border-[var(--border-color)]">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] mb-3">
          Historial de Dependencia IA
        </h3>
        <div className="flex items-end gap-1 h-24">
          {recentSessions.slice(-10).map((session, index) => {
            const height = Math.max(session.ai_dependency * 100, 5);
            return (
              <div
                key={session.session_id}
                className="flex-1 flex flex-col items-center gap-1"
                title={`${new Date(session.date).toLocaleDateString()}: ${Math.round(session.ai_dependency * 100)}%`}
              >
                <div
                  className={`w-full rounded-t transition-all ${
                    session.ai_dependency > 0.7 ? 'bg-red-500' :
                    session.ai_dependency > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ height: `${height}%` }}
                />
                <span className="text-[10px] text-[var(--text-muted)]">
                  {index + 1}
                </span>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-xs text-[var(--text-muted)]">
          <span>Sesiones anteriores</span>
          <span>Sesion mas reciente</span>
        </div>
      </div>

      {/* Tips */}
      <div className={`rounded-lg p-4 border ${
        metrics.isImproving ? 'bg-green-500/10 border-green-500/30' : 'bg-indigo-500/10 border-indigo-500/30'
      }`}>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className={`w-5 h-5 ${metrics.isImproving ? 'text-green-400' : 'text-indigo-400'}`} />
          <h3 className="font-medium text-[var(--text-primary)]">
            Recomendaciones para Ti
          </h3>
        </div>
        <ul className="space-y-2">
          {tips.map((tip, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-[var(--text-muted)]">
              <CheckCircle2 className="w-4 h-4 mt-0.5 text-[var(--text-secondary)]" />
              {tip}
            </li>
          ))}
        </ul>
      </div>

      {/* Achievement indicator */}
      {metrics.avgAIDependency < 0.4 && metrics.stagnationPercent < 20 && (
        <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 rounded-lg p-4 border border-yellow-500/30">
          <div className="flex items-center gap-3">
            <Award className="w-8 h-8 text-yellow-400" />
            <div>
              <h3 className="font-medium text-[var(--text-primary)]">
                Excelente Autonomia
              </h3>
              <p className="text-sm text-[var(--text-muted)]">
                Tu nivel de independencia en la resolucion de problemas es sobresaliente.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StudentCognitiveProfile;
