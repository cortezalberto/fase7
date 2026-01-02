/**
 * LoadingState Component - Loading indicator for training sessions
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = 'Cargando ejercicios...' }: LoadingStateProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4" />
        <p className="text-gray-400">{message}</p>
      </div>
    </div>
  );
}
