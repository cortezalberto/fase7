/**
 * HintDisplay Component - Shows hints and AI corrections
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { Lightbulb, Sparkles } from 'lucide-react';
import type { PistaResponse, CorreccionIAResponse } from '@/services/api';

interface HintDisplayProps {
  hint?: PistaResponse | null;
  aiCorrection?: CorreccionIAResponse | null;
}

export function HintDisplay({ hint, aiCorrection }: HintDisplayProps) {
  return (
    <>
      {hint && (
        <div className="glass rounded-lg p-4 mb-4 bg-yellow-500/5 border border-yellow-500/20">
          <div className="flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-yellow-400 mb-1">
                Pista {hint.numero + 1} de {hint.total_pistas}
              </h4>
              <p className="text-sm text-gray-300">{hint.contenido}</p>
            </div>
          </div>
        </div>
      )}

      {aiCorrection && (
        <div className="glass rounded-lg p-4 mb-4 bg-purple-500/5 border border-purple-500/20">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-purple-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-purple-400 mb-2">Análisis de IA</h4>
              <p className="text-sm text-gray-300 mb-3">{aiCorrection.analisis}</p>
              {aiCorrection.sugerencias.length > 0 && (
                <>
                  <h5 className="text-xs font-semibold text-purple-400 mb-1">Sugerencias:</h5>
                  <ul className="space-y-1">
                    {aiCorrection.sugerencias.map((sug) => (
                      <li key={`sug-${sug.slice(0, 20).replace(/\s/g, '-')}`} className="text-xs text-gray-400 flex items-start gap-2">
                        <span className="text-purple-400">•</span>
                        <span>{sug}</span>
                      </li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
