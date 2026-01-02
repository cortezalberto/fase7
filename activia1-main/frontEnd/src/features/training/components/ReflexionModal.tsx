/**
 * ReflexionModal Component - Post-exercise reflection capture
 *
 * Cortez55: New component for N4 traceability
 * Captures metacognitive reflection after exercises
 */

import { useState, useCallback } from 'react';
import type { ReflexionRequest, ReflexionResponse } from '@/services/api';

interface ReflexionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (reflexion: Omit<ReflexionRequest, 'session_id' | 'exercise_id'>) => Promise<void>;
  loading: boolean;
  lastResponse: ReflexionResponse | null;
  preguntaSeguimiento?: string;
}

export function ReflexionModal({
  isOpen,
  onClose,
  onSubmit,
  loading,
  lastResponse,
  preguntaSeguimiento,
}: ReflexionModalProps) {
  const [queFueDificil, setQueFueDificil] = useState('');
  const [comoLoResolvi, setComoLoResolvi] = useState('');
  const [queAprendi, setQueAprendi] = useState('');
  const [alternativas, setAlternativas] = useState('');
  const [errores, setErrores] = useState('');

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (queFueDificil.length < 10 || comoLoResolvi.length < 10 || queAprendi.length < 10) {
        return;
      }

      await onSubmit({
        que_fue_dificil: queFueDificil,
        como_lo_resolvi: comoLoResolvi,
        que_aprendi: queAprendi,
        alternativas_consideradas: alternativas || undefined,
        errores_cometidos: errores || undefined,
      });

      // Reset form
      setQueFueDificil('');
      setComoLoResolvi('');
      setQueAprendi('');
      setAlternativas('');
      setErrores('');
    },
    [queFueDificil, comoLoResolvi, queAprendi, alternativas, errores, onSubmit]
  );

  if (!isOpen) return null;

  // Show success message if we have a response
  if (lastResponse) {
    return (
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="glass rounded-2xl p-6 max-w-md w-full animate-in fade-in zoom-in duration-300">
          <div className="text-center">
            <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-8 h-8 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Reflexion Registrada</h3>
            <p className="text-gray-300 mb-4">{lastResponse.mensaje}</p>

            <div className="bg-gray-800/50 rounded-xl p-4 mb-4 text-left">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Dimension Cognitiva:</span>
                <span className="text-purple-400 font-medium">
                  {lastResponse.dimension_cognitiva_inferida}
                </span>
              </div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Nivel Metacognitivo:</span>
                <span className="text-blue-400 font-medium">
                  {lastResponse.nivel_metacognitivo}
                </span>
              </div>
              {lastResponse.xp_bonus > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-400">XP Bonus:</span>
                  <span className="text-yellow-400 font-medium">+{lastResponse.xp_bonus} XP</span>
                </div>
              )}
            </div>

            <button
              onClick={onClose}
              className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-colors"
            >
              Continuar
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass rounded-2xl p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-300">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold gradient-text">Reflexion sobre el Ejercicio</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
            aria-label="Cerrar"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {preguntaSeguimiento && (
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <p className="text-purple-300 text-sm">{preguntaSeguimiento}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-white font-medium mb-2">
              Que fue lo mas dificil? <span className="text-red-400">*</span>
            </label>
            <textarea
              value={queFueDificil}
              onChange={(e) => setQueFueDificil(e.target.value)}
              placeholder="Describe que parte del ejercicio te resulto mas desafiante..."
              className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors resize-none"
              rows={3}
              required
              minLength={10}
            />
            <p className="text-gray-500 text-xs mt-1">Minimo 10 caracteres</p>
          </div>

          <div>
            <label className="block text-white font-medium mb-2">
              Como lo resolviste? <span className="text-red-400">*</span>
            </label>
            <textarea
              value={comoLoResolvi}
              onChange={(e) => setComoLoResolvi(e.target.value)}
              placeholder="Explica el proceso que seguiste para resolver el ejercicio..."
              className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors resize-none"
              rows={3}
              required
              minLength={10}
            />
            <p className="text-gray-500 text-xs mt-1">Minimo 10 caracteres</p>
          </div>

          <div>
            <label className="block text-white font-medium mb-2">
              Que aprendiste? <span className="text-red-400">*</span>
            </label>
            <textarea
              value={queAprendi}
              onChange={(e) => setQueAprendi(e.target.value)}
              placeholder="Describe el concepto o habilidad que reforzaste..."
              className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors resize-none"
              rows={3}
              required
              minLength={10}
            />
            <p className="text-gray-500 text-xs mt-1">Minimo 10 caracteres</p>
          </div>

          <div>
            <label className="block text-white font-medium mb-2">
              Alternativas que consideraste <span className="text-gray-500">(opcional)</span>
            </label>
            <textarea
              value={alternativas}
              onChange={(e) => setAlternativas(e.target.value)}
              placeholder="Hubo otras formas de resolver el problema que pensaste?"
              className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors resize-none"
              rows={2}
            />
          </div>

          <div>
            <label className="block text-white font-medium mb-2">
              Errores que cometiste <span className="text-gray-500">(opcional)</span>
            </label>
            <textarea
              value={errores}
              onChange={(e) => setErrores(e.target.value)}
              placeholder="Que errores cometiste y por que crees que ocurrieron?"
              className="w-full bg-gray-800/50 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-colors resize-none"
              rows={2}
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors"
              disabled={loading}
            >
              Omitir
            </button>
            <button
              type="submit"
              className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              disabled={
                loading ||
                queFueDificil.length < 10 ||
                comoLoResolvi.length < 10 ||
                queAprendi.length < 10
              }
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Enviando...
                </>
              ) : (
                'Enviar Reflexion'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
