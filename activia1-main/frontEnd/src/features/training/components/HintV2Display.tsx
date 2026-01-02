/**
 * HintV2Display Component - Display contextual hints from T-IA-Cog
 *
 * Cortez55: New component for N4 traceability
 * Shows contextual hints with help level indicator
 */

import type { PistaV2Response, HelpLevelEnum } from '@/services/api';

interface HintV2DisplayProps {
  hint: PistaV2Response | null;
  className?: string;
  onRequestReflexion?: () => void;
}

// Help level configurations
const helpLevelConfig: Record<
  HelpLevelEnum,
  { label: string; color: string; bgColor: string; description: string; gradient: string }
> = {
  minimo: {
    label: 'Minimo',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    gradient: 'from-green-500 to-emerald-500',
    description: 'Hint muy general, requiere mas trabajo por tu parte',
  },
  bajo: {
    label: 'Bajo',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    gradient: 'from-blue-500 to-cyan-500',
    description: 'Hint con direccion basica',
  },
  medio: {
    label: 'Medio',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    gradient: 'from-yellow-500 to-orange-500',
    description: 'Explicacion conceptual moderada',
  },
  alto: {
    label: 'Alto',
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    gradient: 'from-red-500 to-pink-500',
    description: 'Ayuda detallada (sin solucion completa)',
  },
};

export function HintV2Display({ hint, className = '', onRequestReflexion }: HintV2DisplayProps) {
  if (!hint) return null;

  const levelConfig = helpLevelConfig[hint.nivel_ayuda] || helpLevelConfig.minimo;

  return (
    <div className={`animate-in fade-in slide-in-from-top duration-300 ${className}`}>
      <div className="glass rounded-xl p-4 border border-purple-500/30">
        {/* Header with help level */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-lg bg-gradient-to-br ${levelConfig.gradient} flex items-center justify-center`}
            >
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
            </div>
            <div>
              <span className="text-white font-semibold">
                Pista {hint.numero} de {hint.total_pistas}
              </span>
              <div className="flex items-center gap-2">
                <span className={`${levelConfig.color} text-xs`}>
                  Nivel: {levelConfig.label}
                </span>
              </div>
            </div>
          </div>

          {/* Help level indicator */}
          <div className="flex gap-1">
            {[1, 2, 3, 4].map((level) => (
              <div
                key={level}
                className={`w-2 h-6 rounded-full transition-colors ${
                  level <= hint.numero
                    ? `bg-gradient-to-b ${levelConfig.gradient}`
                    : 'bg-gray-700'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Help level description */}
        <p className="text-xs text-gray-500 mb-3">{levelConfig.description}</p>

        {/* Hint content */}
        <div className="bg-gray-800/50 rounded-lg p-4 mb-3">
          <p className="text-gray-200 whitespace-pre-wrap">{hint.contenido}</p>
        </div>

        {/* Follow-up question if present */}
        {hint.pregunta_seguimiento && (
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 mb-3">
            <div className="flex items-start gap-2">
              <svg
                className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-purple-300 text-sm">{hint.pregunta_seguimiento}</p>
            </div>
          </div>
        )}

        {/* Reflection prompt if required */}
        {hint.requiere_reflexion && onRequestReflexion && (
          <button
            onClick={onRequestReflexion}
            className="w-full py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 text-purple-300 text-sm font-medium transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Agregar Reflexion
          </button>
        )}
      </div>
    </div>
  );
}
