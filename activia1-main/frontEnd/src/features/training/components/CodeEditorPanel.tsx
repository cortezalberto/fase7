/**
 * CodeEditorPanel Component - Code editor with hints and submission
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import Editor from '@monaco-editor/react';
import { Send, ChevronRight, Lightbulb } from 'lucide-react';
import type { PistaResponse, CorreccionIAResponse } from '@/services/api';
import { HintDisplay } from './HintDisplay';

interface CodeEditorPanelProps {
  code: string;
  onCodeChange: (code: string) => void;
  onSubmit: () => void;
  onRequestHint: () => void;
  submitting: boolean;
  loadingHint: boolean;
  currentHint: PistaResponse | null;
  currentHintNumber: number;
  aiCorrection?: CorreccionIAResponse | null;
  hasSession: boolean;
}

export function CodeEditorPanel({
  code,
  onCodeChange,
  onSubmit,
  onRequestHint,
  submitting,
  loadingHint,
  currentHint,
  currentHintNumber,
  aiCorrection,
  hasSession,
}: CodeEditorPanelProps) {
  const isHintDisabled =
    loadingHint ||
    !hasSession ||
    (currentHint !== null && currentHintNumber >= currentHint.total_pistas);

  return (
    <div className="glass rounded-xl p-6">
      <h3 className="text-lg font-bold text-white mb-4">Editor de Código</h3>

      <div
        className="border border-gray-700 rounded-xl overflow-hidden mb-4"
        style={{ height: '400px' }}
      >
        <Editor
          height="100%"
          defaultLanguage="python"
          theme="vs-dark"
          value={code}
          onChange={(value) => onCodeChange(value || '')}
          options={{
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
          }}
        />
      </div>

      <div className="flex gap-3 mb-4">
        <button
          onClick={onRequestHint}
          disabled={isHintDisabled}
          className="flex-1 py-2 px-4 rounded-lg bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-yellow-500/30 transition-colors flex items-center justify-center gap-2"
        >
          {loadingHint ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-400" />
              Cargando...
            </>
          ) : currentHint !== null && currentHintNumber >= currentHint.total_pistas ? (
            <>
              <Lightbulb className="w-4 h-4" />
              Sin más pistas
            </>
          ) : (
            <>
              <Lightbulb className="w-4 h-4" />
              Pista {currentHintNumber + 1}
            </>
          )}
        </button>
      </div>

      <HintDisplay hint={currentHint} aiCorrection={aiCorrection} />

      <button
        onClick={onSubmit}
        disabled={submitting || !code.trim()}
        className="w-full py-3 px-6 rounded-xl gradient-bg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity flex items-center justify-center gap-2"
      >
        {submitting ? (
          <>
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
            Evaluando...
          </>
        ) : (
          <>
            <Send className="w-5 h-5" />
            Enviar Ejercicio
            <ChevronRight className="w-5 h-5" />
          </>
        )}
      </button>
    </div>
  );
}
