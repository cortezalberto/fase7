/**
 * SessionHeader Component - Header with navigation, progress and timer
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { ArrowLeft, Clock } from 'lucide-react';

interface SessionHeaderProps {
  completedExercises: number;
  totalExercises: number;
  timeRemaining: number;
  timeColor: string;
  formatTime: (seconds: number) => string;
  onCancel: () => void;
}

export function SessionHeader({
  completedExercises,
  totalExercises,
  timeRemaining,
  timeColor,
  formatTime,
  onCancel,
}: SessionHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-6">
      <button
        onClick={onCancel}
        className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Cancelar
      </button>

      <div className="flex items-center gap-6">
        <div className="text-center">
          <div className="text-sm text-gray-400">Progreso</div>
          <div className="text-xl font-bold text-white">
            {completedExercises} / {totalExercises}
          </div>
        </div>

        <div className="text-center">
          <div className="text-sm text-gray-400">Tiempo restante</div>
          <div className={`text-2xl font-mono font-bold ${timeColor}`}>
            <Clock className="w-5 h-5 inline mr-2" />
            {formatTime(timeRemaining)}
          </div>
        </div>
      </div>
    </div>
  );
}
