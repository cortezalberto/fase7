/**
 * FinalResults Component - Final results display for training sessions
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { CheckCircle, XCircle, TrendingUp } from 'lucide-react';
import type { ResultadoFinal, ResultadoEjercicio } from '@/services/api';

interface FinalResultsProps {
  result: ResultadoFinal;
  onBack: () => void;
  onRetry: () => void;
}

export function FinalResults({ result, onBack, onRetry }: FinalResultsProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          {result.aprobado ? (
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-green-500/10 mb-4">
              <CheckCircle className="w-16 h-16 text-green-400" />
            </div>
          ) : (
            <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-red-500/10 mb-4">
              <XCircle className="w-16 h-16 text-red-400" />
            </div>
          )}

          <h1 className="text-4xl font-bold gradient-text mb-2">
            {result.aprobado ? '¡Aprobado!' : 'Necesitas mejorar'}
          </h1>
          <p className="text-gray-400">Completaste {result.total_ejercicios} ejercicios</p>
        </div>

        {/* Score Card */}
        <div className="glass rounded-2xl p-8 mb-6">
          <div className="text-center mb-6">
            <div className="text-6xl font-bold gradient-text mb-2">
              {result.nota_final.toFixed(1)}
            </div>
            <p className="text-gray-400">Nota Final</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gray-800/50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-green-400 mb-1">
                {result.ejercicios_correctos}
              </div>
              <p className="text-sm text-gray-400">Correctos</p>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-purple-400 mb-1">
                {result.porcentaje.toFixed(0)}%
              </div>
              <p className="text-sm text-gray-400">Porcentaje</p>
            </div>

            <div className="bg-gray-800/50 rounded-xl p-4 text-center">
              <div className="text-2xl font-bold text-blue-400 mb-1">
                {result.tiempo_usado_min} min
              </div>
              <p className="text-sm text-gray-400">Tiempo usado</p>
            </div>
          </div>
        </div>

        {/* Detailed Results */}
        <div className="glass rounded-xl p-6 mb-6">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-purple-400" />
            Resultados por Ejercicio
          </h3>

          <div className="space-y-3">
            {result.resultados_detalle.map((r: ResultadoEjercicio) => (
              <div
                key={r.numero}
                className="bg-gray-800/50 rounded-lg p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  {r.correcto ? (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400" />
                  )}
                  <span className="text-white font-medium">Ejercicio {r.numero}</span>
                </div>
                <div className="text-sm text-gray-400">
                  {r.tests_pasados}/{r.tests_totales} tests
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={onBack}
            className="flex-1 py-3 px-6 rounded-xl bg-gray-700 text-white font-medium hover:bg-gray-600 transition-colors"
          >
            Volver al menú
          </button>
          <button
            onClick={onRetry}
            className="flex-1 py-3 px-6 rounded-xl gradient-bg text-white font-medium hover:opacity-90 transition-opacity"
          >
            Intentar de nuevo
          </button>
        </div>
      </div>
    </div>
  );
}
