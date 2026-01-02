/**
 * SimulatorGrid Component - Simulator selection view
 *
 * Cortez43: Extracted from SimulatorsPage.tsx (514 lines)
 */

import { Users } from 'lucide-react';
import type { Simulator } from '@/types';
import { SimulatorCard } from './SimulatorCard';

interface SimulatorGridProps {
  simulators: Simulator[];
  onSelectSimulator: (simulator: Simulator) => void;
}

export function SimulatorGrid({ simulators, onSelectSimulator }: SimulatorGridProps) {
  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-[var(--text-primary)] mb-2">
          Simuladores Profesionales
        </h1>
        <p className="text-[var(--text-secondary)]">
          Practica situaciones reales del mundo laboral con IA
        </p>
      </div>

      {/* Info Card */}
      <div className="bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10 rounded-2xl border border-[var(--accent-primary)]/20 p-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Users className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-[var(--text-primary)] mb-2">
              ¿Qué son los simuladores?
            </h3>
            <p className="text-[var(--text-secondary)]">
              Los simuladores te permiten practicar interacciones profesionales reales. Cada
              simulador adopta un rol específico (Product Owner, Scrum Master, etc.) y evalúa
              tus competencias transversales como comunicación, análisis y resolución de
              problemas.
            </p>
          </div>
        </div>
      </div>

      {/* Simulators Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {simulators.map((simulator) => (
          <SimulatorCard
            key={simulator.type}
            simulator={simulator}
            onSelect={onSelectSimulator}
          />
        ))}
      </div>
    </div>
  );
}
