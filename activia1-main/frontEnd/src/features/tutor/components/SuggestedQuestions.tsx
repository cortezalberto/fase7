/**
 * SuggestedQuestions Component - Quick question suggestions
 *
 * Cortez43: Extracted from TutorPage.tsx (605 lines)
 */

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
  visible?: boolean;
}

const SUGGESTED_QUESTIONS = [
  '¿Cómo implemento una cola circular?',
  'Explícame el patrón Observer',
  '¿Cuál es la diferencia entre stack y heap?',
  'Ayúdame con recursión',
];

export function SuggestedQuestions({ onSelect, visible = true }: SuggestedQuestionsProps) {
  if (!visible) return null;

  return (
    <div className="mt-4">
      <p className="text-sm text-[var(--text-muted)] mb-3">Preguntas sugeridas:</p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((question, i) => (
          <button
            key={i}
            onClick={() => onSelect(question)}
            className="px-4 py-2 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border-color)] text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent-primary)] transition-all"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
