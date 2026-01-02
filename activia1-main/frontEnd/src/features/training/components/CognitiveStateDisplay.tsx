/**
 * CognitiveStateDisplay Component - Show inferred cognitive state
 *
 * Cortez55: New component for N4 traceability
 * Displays the student's current cognitive state as inferred by the system
 */

import type { CognitiveStateEnum } from '@/services/api';

interface CognitiveStateDisplayProps {
  state: CognitiveStateEnum | null;
  className?: string;
  showLabel?: boolean;
}

// State configurations
const stateConfig: Record<
  CognitiveStateEnum,
  { label: string; color: string; bgColor: string; icon: string; description: string }
> = {
  inicio: {
    label: 'Inicio',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    description: 'Comenzando el ejercicio',
  },
  exploracion: {
    label: 'Exploracion',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
    icon: 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
    description: 'Explorando el problema',
  },
  implementacion: {
    label: 'Implementacion',
    color: 'text-green-400',
    bgColor: 'bg-green-500/20',
    icon: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    description: 'Escribiendo codigo',
  },
  depuracion: {
    label: 'Depuracion',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/20',
    icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    description: 'Corrigiendo errores',
  },
  depuracion_sintaxis: {
    label: 'Sintaxis',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
    description: 'Corrigiendo errores de sintaxis',
  },
  cambio_estrategia: {
    label: 'Cambio Estrategia',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    icon: 'M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4',
    description: 'Cambiando de enfoque',
  },
  validacion: {
    label: 'Validacion',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
    icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    description: 'Verificando solucion',
  },
  estancamiento: {
    label: 'Estancamiento',
    color: 'text-red-400',
    bgColor: 'bg-red-500/20',
    icon: 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636',
    description: 'Necesita ayuda',
  },
  reflexion: {
    label: 'Reflexion',
    color: 'text-indigo-400',
    bgColor: 'bg-indigo-500/20',
    icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    description: 'Reflexionando sobre el proceso',
  },
};

export function CognitiveStateDisplay({
  state,
  className = '',
  showLabel = true,
}: CognitiveStateDisplayProps) {
  if (!state) return null;

  const config = stateConfig[state] || {
    label: state,
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/20',
    icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    description: 'Estado desconocido',
  };

  return (
    <div
      className={`flex items-center gap-2 ${className}`}
      title={config.description}
    >
      <div className={`${config.bgColor} ${config.color} p-1.5 rounded-lg`}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={config.icon} />
        </svg>
      </div>
      {showLabel && (
        <span className={`${config.color} text-sm font-medium`}>{config.label}</span>
      )}
    </div>
  );
}

// Compact badge version
export function CognitiveStateBadge({ state }: { state: CognitiveStateEnum | null }) {
  if (!state) return null;

  const config = stateConfig[state];
  if (!config) return null;

  return (
    <span
      className={`${config.bgColor} ${config.color} text-xs font-medium px-2 py-1 rounded-full inline-flex items-center gap-1`}
      title={config.description}
    >
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={config.icon} />
      </svg>
      {config.label}
    </span>
  );
}
