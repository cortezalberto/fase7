/**
 * Dynamic Style Utilities
 *
 * FIX Cortez71 LOW-001: Centralized dynamic style functions
 *
 * Note: Some inline styles are necessary for dynamic values (percentages, colors)
 * These utilities standardize how we handle them.
 */

/**
 * Generate progress bar width style
 * @param percentage - Value from 0-100
 */
export function progressWidth(percentage: number): React.CSSProperties {
  const clampedValue = Math.max(0, Math.min(100, percentage));
  return { width: `${clampedValue}%` };
}

/**
 * Generate dynamic color styles for themed elements
 * @param color - CSS color value (hex, rgb, etc.)
 */
export function themedBorder(color: string): React.CSSProperties {
  return {
    borderColor: `${color}40`,
    backgroundColor: `${color}08`,
  };
}

/**
 * Generate badge/chip background style
 * @param color - CSS color value
 */
export function themedBadge(color: string): React.CSSProperties {
  return {
    backgroundColor: `${color}20`,
    border: `2px solid ${color}`,
  };
}

/**
 * Generate text color style
 * @param color - CSS color value
 */
export function textColor(color: string): React.CSSProperties {
  return { color };
}

/**
 * Generate background color style
 * @param color - CSS color value
 */
export function bgColor(color: string): React.CSSProperties {
  return { backgroundColor: color };
}

/**
 * Score to percentage for progress bars (0-10 scale)
 */
export function scoreToWidth(score: number, maxScore = 10): React.CSSProperties {
  const percentage = (score / maxScore) * 100;
  return progressWidth(percentage);
}

/**
 * Combined styles for styled components
 */
export function combineStyles(...styles: React.CSSProperties[]): React.CSSProperties {
  return Object.assign({}, ...styles);
}
