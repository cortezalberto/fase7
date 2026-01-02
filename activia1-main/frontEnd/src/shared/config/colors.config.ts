/**
 * Colors Configuration - Consistent color schemes across the app
 *
 * Cortez43: Centralized color configuration for consistency
 */

// Risk Level Colors (Tailwind classes)
export const RiskLevelColors: Record<string, string> = {
  info: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  low: 'text-green-400 bg-green-500/10 border-green-500/20',
  medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  high: 'text-orange-400 bg-orange-500/10 border-orange-500/20',
  critical: 'text-red-400 bg-red-500/10 border-red-500/20',
};

// Risk Level Background Colors
export const RiskLevelBgColors: Record<string, string> = {
  info: 'bg-blue-500',
  low: 'bg-green-500',
  medium: 'bg-yellow-500',
  high: 'bg-orange-500',
  critical: 'bg-red-500',
};

// Status Colors
export const StatusColors: Record<string, string> = {
  active: 'text-green-400 bg-green-500/10',
  paused: 'text-yellow-400 bg-yellow-500/10',
  completed: 'text-blue-400 bg-blue-500/10',
  abandoned: 'text-gray-400 bg-gray-500/10',
  development: 'text-yellow-400 bg-yellow-500/10',
};

// Progress Colors
export const ProgressColors: Record<string, string> = {
  low: 'bg-red-500',
  medium: 'bg-yellow-500',
  high: 'bg-green-500',
  complete: 'bg-purple-500',
};

// Gradient Presets
export const GradientPresets = {
  primary: 'from-indigo-500 to-purple-600',
  success: 'from-green-500 to-emerald-600',
  warning: 'from-yellow-500 to-orange-600',
  danger: 'from-red-500 to-rose-600',
  info: 'from-blue-500 to-cyan-600',
  purple: 'from-purple-500 to-pink-600',
} as const;

// Cognitive State Colors
export const CognitiveStateColors: Record<string, string> = {
  exploring: 'text-blue-400 bg-blue-500/10',
  confused: 'text-yellow-400 bg-yellow-500/10',
  progressing: 'text-green-400 bg-green-500/10',
  stuck: 'text-orange-400 bg-orange-500/10',
  mastering: 'text-purple-400 bg-purple-500/10',
  frustrated: 'text-red-400 bg-red-500/10',
};

// Chart Color Palettes
export const ChartColors = {
  primary: ['#8B5CF6', '#A78BFA', '#C4B5FD', '#DDD6FE', '#EDE9FE'],
  success: ['#10B981', '#34D399', '#6EE7B7', '#A7F3D0', '#D1FAE5'],
  warning: ['#F59E0B', '#FBBF24', '#FCD34D', '#FDE68A', '#FEF3C7'],
  danger: ['#EF4444', '#F87171', '#FCA5A5', '#FECACA', '#FEE2E2'],
  rainbow: ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
} as const;

// Dimension Colors (for risk dimensions)
export const DimensionColors: Record<string, string> = {
  academic_integrity: '#8B5CF6',
  cognitive_development: '#3B82F6',
  learning_quality: '#10B981',
  autonomy_level: '#F59E0B',
  emotional_wellbeing: '#EC4899',
};
