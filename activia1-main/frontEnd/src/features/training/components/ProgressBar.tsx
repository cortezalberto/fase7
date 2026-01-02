/**
 * ProgressBar Component - Exercise progress visualization
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

interface ProgressBarProps {
  totalExercises: number;
  completedExercises: number;
}

export function ProgressBar({ totalExercises, completedExercises }: ProgressBarProps) {
  return (
    <div className="flex gap-1">
      {Array.from({ length: totalExercises }).map((_, i) => (
        <div
          key={i}
          className={`flex-1 h-2 rounded-full transition-colors ${
            i < completedExercises
              ? 'bg-green-500'
              : i === completedExercises
              ? 'bg-purple-500 animate-pulse'
              : 'bg-gray-700'
          }`}
        />
      ))}
    </div>
  );
}
