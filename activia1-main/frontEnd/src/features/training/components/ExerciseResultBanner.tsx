/**
 * ExerciseResultBanner Component - Shows result after exercise submission
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { CheckCircle, XCircle } from 'lucide-react';
import type { ResultadoEjercicio } from '@/services/api';

interface ExerciseResultBannerProps {
  result: ResultadoEjercicio;
}

export function ExerciseResultBanner({ result }: ExerciseResultBannerProps) {
  return (
    <div
      className={`glass rounded-xl p-6 mb-6 border-l-4 ${
        result.correcto ? 'border-green-500' : 'border-red-500'
      }`}
    >
      <div className="flex items-center gap-4">
        {result.correcto ? (
          <CheckCircle className="w-8 h-8 text-green-400" />
        ) : (
          <XCircle className="w-8 h-8 text-red-400" />
        )}
        <div>
          <h3 className="text-lg font-bold text-white">
            {result.correcto ? '¡Correcto!' : 'Incorrecto'}
          </h3>
          <p className="text-gray-400">
            {result.tests_pasados}/{result.tests_totales} tests pasados
          </p>
        </div>
      </div>
    </div>
  );
}
