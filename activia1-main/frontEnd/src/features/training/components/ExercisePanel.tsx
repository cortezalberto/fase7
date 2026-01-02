/**
 * ExercisePanel Component - Exercise instructions display
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import ReactMarkdown from 'react-markdown';
import type { Components } from 'react-markdown';
import type { EjercicioActual } from '@/services/api';

interface ExercisePanelProps {
  exercise: EjercicioActual;
  topic: string;
}

// Markdown component styling
const markdownComponents: Components = {
  h1: ({ ...props }) => <h1 className="text-2xl font-bold text-white mb-3" {...props} />,
  h2: ({ ...props }) => <h2 className="text-xl font-bold text-white mb-2 mt-4" {...props} />,
  h3: ({ ...props }) => <h3 className="text-lg font-semibold text-white mb-2 mt-3" {...props} />,
  h4: ({ ...props }) => <h4 className="text-base font-semibold text-gray-200 mb-1 mt-2" {...props} />,
  p: ({ ...props }) => <p className="text-gray-300 mb-2 leading-relaxed" {...props} />,
  ul: ({ ...props }) => <ul className="list-disc list-inside text-gray-300 mb-2 space-y-1" {...props} />,
  ol: ({ ...props }) => <ol className="list-decimal list-inside text-gray-300 mb-2 space-y-1" {...props} />,
  li: ({ ...props }) => <li className="text-gray-300" {...props} />,
  code: ({ className, children, ...props }) => {
    const isInline = !className?.includes('language-');
    return isInline ? (
      <code
        className="bg-gray-700/50 text-purple-400 px-1.5 py-0.5 rounded text-sm font-mono"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        className="block bg-gray-900 text-gray-300 p-3 rounded-lg overflow-x-auto text-sm font-mono my-2"
        {...props}
      >
        {children}
      </code>
    );
  },
  strong: ({ ...props }) => <strong className="font-bold text-white" {...props} />,
  em: ({ ...props }) => <em className="italic text-gray-200" {...props} />,
  blockquote: ({ ...props }) => (
    <blockquote className="border-l-4 border-purple-500 pl-4 italic text-gray-400 my-2" {...props} />
  ),
};

export function ExercisePanel({ exercise, topic }: ExercisePanelProps) {
  return (
    <div className="glass rounded-xl p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-2xl font-bold gradient-text">Ejercicio {exercise.numero}</h2>
          <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-sm font-medium">
            {topic}
          </span>
        </div>
      </div>

      <div className="bg-gray-800/50 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-3">Consigna:</h3>
        <div className="prose prose-invert prose-sm max-w-none text-gray-300">
          <ReactMarkdown components={markdownComponents}>
            {exercise.consigna || ''}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
