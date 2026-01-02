/**
 * SimulatorsPage - Professional simulators page
 *
 * Cortez43: Refactored from 514 lines to ~50 lines
 * Extracted: useSimulatorSession hook
 * Extracted: SimulatorCard, SimulatorChatView, SimulatorGrid components
 * Extracted: simulatorConfig (icons, colors, messages)
 */

import { Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import {
  SimulatorGrid,
  SimulatorChatView,
  useSimulatorSession,
} from '../features/simulators';

export default function SimulatorsPage() {
  const { user } = useAuth();

  const simulator = useSimulatorSession({
    userId: user?.id || 'guest',
  });

  // Loading state
  if (simulator.isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 text-[var(--accent-primary)] animate-spin" />
      </div>
    );
  }

  // Active simulation view
  if (simulator.selectedSimulator && simulator.session) {
    return (
      <SimulatorChatView
        simulator={simulator.selectedSimulator}
        messages={simulator.messages}
        input={simulator.input}
        isSending={simulator.isSending}
        onInputChange={simulator.setInput}
        onSendMessage={simulator.sendMessage}
        onClose={simulator.closeSimulation}
      />
    );
  }

  // Simulator selection view
  return (
    <SimulatorGrid
      simulators={simulator.simulators}
      onSelectSimulator={simulator.startSimulation}
    />
  );
}
