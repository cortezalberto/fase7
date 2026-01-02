/**
 * SimulatorCard Component - Simulator selection card
 *
 * Cortez43: Extracted from SimulatorsPage.tsx (514 lines)
 */

import { ArrowRight, Users, type LucideIcon } from 'lucide-react';
import type { Simulator } from '@/types';
import { simulatorIcons, simulatorColors } from '../config/simulatorConfig';

interface SimulatorCardProps {
  simulator: Simulator;
  onSelect: (simulator: Simulator) => void;
}

export function SimulatorCard({ simulator, onSelect }: SimulatorCardProps) {
  const Icon: LucideIcon = simulatorIcons[simulator.type] || Users;
  const colorClass = simulatorColors[simulator.type] || 'from-gray-500 to-gray-600';
  const isAvailable = simulator.status === 'active';

  return (
    <div
      role="button"
      tabIndex={isAvailable ? 0 : -1}
      aria-disabled={!isAvailable}
      aria-label={`${simulator.name}. ${isAvailable ? 'Click para iniciar simulación' : 'No disponible'}`}
      className={`bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] p-6 transition-all duration-300 ${
        isAvailable
          ? 'hover:border-[var(--accent-primary)]/50 hover:shadow-lg hover:shadow-[var(--accent-primary)]/10 cursor-pointer'
          : 'opacity-60'
      }`}
      onClick={() => isAvailable && onSelect(simulator)}
      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && isAvailable && onSelect(simulator)}
    >
      <div className="flex items-start justify-between mb-4">
        <div
          className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${colorClass} flex items-center justify-center`}
        >
          <Icon className="w-7 h-7 text-white" />
        </div>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium ${
            isAvailable
              ? 'bg-green-500/10 text-green-400'
              : 'bg-yellow-500/10 text-yellow-400'
          }`}
        >
          {isAvailable ? 'Disponible' : 'En desarrollo'}
        </span>
      </div>

      <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
        {simulator.name}
      </h3>
      <p className="text-sm text-[var(--text-secondary)] mb-4">{simulator.description}</p>

      <div className="pt-4 border-t border-[var(--border-color)]">
        <p className="text-xs text-[var(--text-muted)] mb-2">Competencias:</p>
        <div className="flex flex-wrap gap-1">
          {simulator.competencies.slice(0, 3).map((comp) => (
            <span
              key={`${simulator.type}-comp-${comp}`}
              className="px-2 py-0.5 rounded text-xs bg-[var(--bg-tertiary)] text-[var(--text-secondary)]"
            >
              {comp.replace('_', ' ')}
            </span>
          ))}
        </div>
      </div>

      {isAvailable && (
        <div className="flex items-center justify-end mt-4 text-[var(--accent-primary)] text-sm font-medium">
          Iniciar simulación
          <ArrowRight className="w-4 h-4 ml-2" />
        </div>
      )}
    </div>
  );
}
