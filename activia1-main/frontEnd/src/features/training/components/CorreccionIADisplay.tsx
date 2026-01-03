/**
 * CorreccionIADisplay - AI Correction feedback display
 *
 * Cortez56: Component to display AI-powered code correction and suggestions
 *
 * Features:
 * - Shows AI analysis of student code
 * - Displays improvement suggestions (max 4)
 * - Shows test results summary with progress bar
 * - Indicates pass/fail status
 */

import { CorreccionIAResponse, ResultadoEjercicio } from '@/services/api';

export interface CorreccionIADisplayProps {
  correccion: CorreccionIAResponse;
  onClose?: () => void;
  className?: string;
}

/**
 * Main display component for AI correction results
 */
export function CorreccionIADisplay({
  correccion,
  onClose,
  className = '',
}: CorreccionIADisplayProps) {
  const { analisis, sugerencias, porcentaje, aprobado, tiempo_usado_min, resultados_detalle } =
    correccion;

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-2xl">🤖</span>
          Feedback de IA
        </h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            aria-label="Cerrar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Status Badge */}
      <div className="mb-4">
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            aprobado
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
          }`}
        >
          {aprobado ? '✓ Aprobado' : '⚠ Necesita mejoras'}
        </span>
        <span className="ml-3 text-sm text-gray-500 dark:text-gray-400">
          {tiempo_usado_min} min transcurridos
        </span>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600 dark:text-gray-400">Progreso</span>
          <span className="font-medium text-gray-900 dark:text-white">{porcentaje.toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full transition-all duration-500 ${
              porcentaje >= 60 ? 'bg-green-500' : porcentaje >= 40 ? 'bg-yellow-500' : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(porcentaje, 100)}%` }}
          />
        </div>
      </div>

      {/* Analysis Section */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
          <span>📝</span> Analisis
        </h4>
        <p className="text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          {analisis}
        </p>
      </div>

      {/* Suggestions Section */}
      {sugerencias.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
            <span>💡</span> Sugerencias de mejora
          </h4>
          {/* FIX Cortez71 HIGH-001: Use stable key based on content + index */}
          <ul className="space-y-2">
            {sugerencias.map((sugerencia, index) => (
              <li
                key={`sugerencia-${index}-${sugerencia.slice(0, 20)}`}
                className="flex items-start gap-2 text-gray-600 dark:text-gray-400"
              >
                <span className="flex-shrink-0 w-5 h-5 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 rounded-full flex items-center justify-center text-xs font-medium">
                  {index + 1}
                </span>
                <span>{sugerencia}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Test Results Detail */}
      {resultados_detalle.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
            <span>🧪</span> Resultados de tests
          </h4>
          <div className="space-y-2">
            {resultados_detalle.map((resultado) => (
              <TestResultItem key={resultado.numero} resultado={resultado} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Individual test result item
 */
function TestResultItem({ resultado }: { resultado: ResultadoEjercicio }) {
  const { numero, correcto, tests_pasados, tests_totales, mensaje } = resultado;

  return (
    <div
      className={`flex items-center justify-between p-3 rounded-lg border ${
        correcto
          ? 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20'
          : 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20'
      }`}
    >
      <div className="flex items-center gap-3">
        <span className={correcto ? 'text-green-500' : 'text-red-500'}>
          {correcto ? '✓' : '✗'}
        </span>
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Ejercicio {numero}
        </span>
      </div>
      <div className="text-right">
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {tests_pasados}/{tests_totales} tests
        </span>
        <p className="text-xs text-gray-500 dark:text-gray-500">{mensaje}</p>
      </div>
    </div>
  );
}

/**
 * Compact badge version for inline display
 */
export function CorreccionIABadge({
  correccion,
  onClick,
}: {
  correccion: CorreccionIAResponse;
  onClick?: () => void;
}) {
  const { porcentaje, aprobado } = correccion;

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
        aprobado
          ? 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300'
          : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200 dark:bg-yellow-900 dark:text-yellow-300'
      }`}
    >
      <span>🤖</span>
      <span>{porcentaje.toFixed(0)}%</span>
      {aprobado ? <span>✓</span> : <span>⚠</span>}
    </button>
  );
}

/**
 * Modal wrapper for CorreccionIADisplay
 */
export function CorreccionIAModal({
  isOpen,
  correccion,
  onClose,
}: {
  isOpen: boolean;
  correccion: CorreccionIAResponse | null;
  onClose: () => void;
}) {
  if (!isOpen || !correccion) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative z-10 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CorreccionIADisplay correccion={correccion} onClose={onClose} />
      </div>
    </div>
  );
}

export default CorreccionIADisplay;
