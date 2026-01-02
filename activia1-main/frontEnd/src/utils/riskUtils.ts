/**
 * Risk Utilities
 * FIX Cortez32: Moved pure functions outside components to prevent recreation on each render
 *
 * These utility functions are used by:
 * - RiskAnalysisViewer
 * - RiskMonitorPanel
 * - Any component that needs to display risk information
 */

export interface RiskColorClasses {
  bg: string;
  border: string;
  text: string;
  bar?: string;
}

/**
 * Get CSS classes for a given risk level
 * FIX Cortez32: Moved outside component to prevent recreation
 */
export const getRiskColor = (level: string): RiskColorClasses => {
  switch (level) {
    case 'info':
      return { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', bar: 'bg-blue-500' };
    case 'low':
      return { bg: 'bg-green-500/10', border: 'border-green-500/30', text: 'text-green-400', bar: 'bg-green-500' };
    case 'medium':
      return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', bar: 'bg-yellow-500' };
    case 'high':
      return { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', bar: 'bg-orange-500' };
    case 'critical':
      return { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', bar: 'bg-red-500' };
    default:
      return { bg: 'bg-gray-500/10', border: 'border-gray-500/30', text: 'text-gray-400', bar: 'bg-gray-500' };
  }
};

/**
 * Get icon for a risk dimension
 * FIX Cortez32: Moved outside component to prevent recreation
 */
export const getDimensionIcon = (dimension: string): string => {
  switch (dimension) {
    case 'cognitive':
      return '🧠';
    case 'ethical':
      return '⚖️';
    case 'epistemic':
      return '📚';
    case 'technical':
      return '⚙️';
    case 'governance':
      return '🏛️';
    default:
      return '🔍';
  }
};

/**
 * Get localized title for a risk dimension
 * FIX Cortez32: Moved outside component to prevent recreation
 */
export const getDimensionTitle = (dimension: string): string => {
  switch (dimension) {
    case 'cognitive':
      return 'Cognitiva';
    case 'ethical':
      return 'Ética';
    case 'epistemic':
      return 'Epistémica';
    case 'technical':
      return 'Técnica';
    case 'governance':
      return 'Gobernanza';
    default:
      return dimension;
  }
};

/**
 * Dimension configuration for panels
 */
export const DIMENSION_CONFIG: Record<string, { icon: string; name: string; color: string }> = {
  cognitive: { icon: '🧠', name: 'Cognitiva', color: 'text-purple-400' },
  ethical: { icon: '⚖️', name: 'Ética', color: 'text-blue-400' },
  epistemic: { icon: '📚', name: 'Epistémica', color: 'text-cyan-400' },
  technical: { icon: '⚙️', name: 'Técnica', color: 'text-orange-400' },
  governance: { icon: '🏛️', name: 'Gobernanza', color: 'text-green-400' }
};

/**
 * Get gradient class for progress bar based on risk level
 */
export const getRiskGradient = (level: string): string => {
  switch (level) {
    case 'info':
    case 'low':
      return 'bg-gradient-to-r from-green-500 to-emerald-500';
    case 'medium':
      return 'bg-gradient-to-r from-yellow-500 to-orange-500';
    case 'high':
      return 'bg-gradient-to-r from-orange-500 to-red-500';
    case 'critical':
      return 'bg-gradient-to-r from-red-500 to-rose-500';
    default:
      return 'bg-gradient-to-r from-gray-500 to-gray-600';
  }
};
