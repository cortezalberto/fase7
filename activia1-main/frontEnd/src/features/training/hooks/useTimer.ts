/**
 * useTimer Hook - Timer management for training sessions
 *
 * Cortez43: Extracted from TrainingExamPage.tsx (638 lines)
 */

import { useState, useRef, useCallback, useEffect } from 'react';

export interface UseTimerOptions {
  initialTime: number;
  onTimeUp?: () => void;
}

export interface UseTimerReturn {
  timeRemaining: number;
  isRunning: boolean;
  formatTime: (seconds: number) => string;
  getTimeColor: () => string;
  startTimer: (endTime: Date) => void;
  stopTimer: () => void;
  resetTimer: () => void;
}

export function useTimer({ initialTime = 0, onTimeUp }: UseTimerOptions): UseTimerReturn {
  const [timeRemaining, setTimeRemaining] = useState<number>(initialTime);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const timerRef = useRef<number | null>(null);
  const timeUpCalledRef = useRef<boolean>(false);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setIsRunning(false);
  }, []);

  const startTimer = useCallback((endTime: Date) => {
    stopTimer();
    timeUpCalledRef.current = false;

    const endTimestamp = endTime.getTime();
    const remaining = Math.floor((endTimestamp - Date.now()) / 1000);
    setTimeRemaining(remaining);
    setIsRunning(true);

    timerRef.current = window.setInterval(() => {
      setTimeRemaining((prev) => {
        if (prev <= 1) {
          if (!timeUpCalledRef.current) {
            timeUpCalledRef.current = true;
            onTimeUp?.();
          }
          stopTimer();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  }, [onTimeUp, stopTimer]);

  const resetTimer = useCallback(() => {
    stopTimer();
    setTimeRemaining(initialTime);
    timeUpCalledRef.current = false;
  }, [initialTime, stopTimer]);

  // Format time as MM:SS
  const formatTime = useCallback((seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Get color based on remaining time
  const getTimeColor = useCallback((): string => {
    if (timeRemaining > 600) return 'text-green-400';
    if (timeRemaining > 300) return 'text-yellow-400';
    return 'text-red-400 animate-pulse';
  }, [timeRemaining]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return {
    timeRemaining,
    isRunning,
    formatTime,
    getTimeColor,
    startTimer,
    stopTimer,
    resetTimer,
  };
}
