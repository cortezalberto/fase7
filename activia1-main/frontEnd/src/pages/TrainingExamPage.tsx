/**
 * TrainingExamPage - Training exam session page
 *
 * Cortez43: Refactored from 638 lines to ~120 lines
 * Extracted: useTimer, useTrainingSession hooks
 * Extracted: LoadingState, ErrorState, FinalResults, ProgressBar,
 *            ExerciseResultBanner, ExercisePanel, CodeEditorPanel, SessionHeader
 */

import { useEffect, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useToast } from '../shared/components/Toast/Toast';
import {
  LoadingState,
  ErrorState,
  FinalResults,
  ProgressBar,
  ExerciseResultBanner,
  ExercisePanel,
  CodeEditorPanel,
  SessionHeader,
} from '../features/training/components';
import { useTimer, useTrainingSession } from '../features/training/hooks';

const TrainingExamPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { showToast } = useToast();

  const { language, unit_number, exercise_id } = location.state || {};

  // Timer callback
  const handleTimeUp = useCallback(() => {
    showToast('¡Tiempo agotado! La sesión ha terminado.', 'warning');
    navigate('/training');
  }, [navigate, showToast]);

  // Custom hooks
  const timer = useTimer({ initialTime: 0, onTimeUp: handleTimeUp });

  const training = useTrainingSession({
    language,
    unit_number,
    exercise_id,
  });

  // Initialize session on mount
  const { initSession } = training;
  const { startTimer, stopTimer } = timer;
  useEffect(() => {
    if (!language || !unit_number) {
      navigate('/training');
      return;
    }

    const init = async () => {
      const endTime = await initSession();
      if (endTime) {
        startTimer(endTime);
      }
    };

    init();

    return () => {
      stopTimer();
    };
  }, [language, unit_number, navigate, initSession, startTimer, stopTimer]);

  // Handle retry
  const handleRetry = async () => {
    training.resetSession();
    timer.resetTimer();
    const endTime = await training.initSession();
    if (endTime) {
      timer.startTimer(endTime);
    }
  };

  // Loading state
  if (training.loading) {
    return <LoadingState />;
  }

  // Error state
  if (training.error && !training.session) {
    return (
      <ErrorState
        error={training.error}
        onBack={() => navigate('/training')}
      />
    );
  }

  // Session not loaded
  if (!training.session || !training.currentExercise) {
    return <LoadingState />;
  }

  // Final results
  if (training.finalResult) {
    return (
      <FinalResults
        result={training.finalResult}
        onBack={() => navigate('/training')}
        onRetry={handleRetry}
      />
    );
  }

  // Main training view
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        <SessionHeader
          completedExercises={training.completedExercises}
          totalExercises={training.session.total_ejercicios}
          timeRemaining={timer.timeRemaining}
          timeColor={timer.getTimeColor()}
          formatTime={timer.formatTime}
          onCancel={() => navigate('/training')}
        />

        <div className="mb-6">
          <ProgressBar
            totalExercises={training.session.total_ejercicios}
            completedExercises={training.completedExercises}
          />
        </div>

        {training.showExerciseResult && training.lastResult && (
          <ExerciseResultBanner result={training.lastResult} />
        )}

        {training.error && (
          <div className="glass rounded-xl p-4 mb-6 bg-red-500/10 border border-red-500/20">
            <p className="text-red-400">{training.error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ExercisePanel
            exercise={training.currentExercise}
            topic={training.session.tema}
          />

          <CodeEditorPanel
            code={training.code}
            onCodeChange={training.setCode}
            onSubmit={training.submitExercise}
            onRequestHint={training.requestHint}
            submitting={training.submitting}
            loadingHint={training.loadingHint}
            currentHint={training.currentHint}
            currentHintNumber={training.currentHintNumber}
            hasSession={!!training.session}
          />
        </div>
      </div>
    </div>
  );
};

export default TrainingExamPage;
