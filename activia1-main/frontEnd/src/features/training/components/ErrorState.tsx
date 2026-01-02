/**
 * ErrorState Component - Error display for training sessions
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { XCircle } from 'lucide-react';

interface ErrorStateProps {
  error: string;
  onBack: () => void;
  backLabel?: string;
}

export function ErrorState({ error, onBack, backLabel = 'Volver al menú' }: ErrorStateProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center p-6">
      <div className="max-w-md glass rounded-xl p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-6 bg-red-500/10 rounded-full flex items-center justify-center">
          <XCircle className="w-8 h-8 text-red-400" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">Error al cargar</h2>
        <p className="text-gray-400 mb-6">{error}</p>
        <button
          onClick={onBack}
          className="w-full py-3 px-6 rounded-xl gradient-bg text-white font-medium hover:opacity-90 transition-opacity"
        >
          {backLabel}
        </button>
      </div>
    </div>
  );
}
