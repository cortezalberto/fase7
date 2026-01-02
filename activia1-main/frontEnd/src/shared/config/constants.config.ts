/**
 * Constants Configuration - Application-wide constants
 *
 * Cortez43: Centralized constants for consistency
 */

// Timer Constants (in seconds)
export const TIMER_THRESHOLDS = {
  SAFE: 600, // > 10 minutes = green
  WARNING: 300, // > 5 minutes = yellow
  DANGER: 0, // <= 5 minutes = red
} as const;

// Pagination Defaults
export const PAGINATION_DEFAULTS = {
  PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [5, 10, 20, 50],
  INITIAL_PAGE: 1,
} as const;

// Chat Constants
export const CHAT_CONSTANTS = {
  MAX_MESSAGE_LENGTH: 5000,
  MAX_CONVERSATION_HISTORY: 10,
  TYPING_INDICATOR_DELAY: 500,
  AUTO_SCROLL_DELAY: 100,
} as const;

// Session Constants
export const SESSION_CONSTANTS = {
  DEFAULT_TIMEOUT_MINUTES: 30,
  IDLE_WARNING_MINUTES: 5,
  MAX_IDLE_MINUTES: 10,
} as const;

// Risk Analysis Constants
export const RISK_CONSTANTS = {
  UPDATE_DEBOUNCE_MS: 2000,
  MAX_TOP_RISKS: 5,
  SCORE_THRESHOLDS: {
    LOW: 30,
    MEDIUM: 60,
    HIGH: 80,
    CRITICAL: 90,
  },
} as const;

// Animation Durations (in milliseconds)
export const ANIMATION_DURATIONS = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000,
} as const;

// Breakpoints (matching Tailwind defaults)
export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  XXL: 1536,
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
  USER: 'user',
  THEME: 'theme',
  SIDEBAR_COLLAPSED: 'sidebar_collapsed',
  LANGUAGE: 'language',
} as const;

// HTTP Constants
export const HTTP_CONSTANTS = {
  TIMEOUT: 30000,
  RETRY_ATTEMPTS: 3,
  CIRCUIT_BREAKER_THRESHOLD: 5,
  CIRCUIT_RESET_TIME: 60000,
} as const;

// Editor Constants (Monaco)
export const EDITOR_CONSTANTS = {
  DEFAULT_LANGUAGE: 'python',
  DEFAULT_THEME: 'vs-dark',
  FONT_SIZE: 14,
  TAB_SIZE: 4,
  MIN_HEIGHT: 300,
  MAX_HEIGHT: 600,
} as const;

// Validation Constants
export const VALIDATION_CONSTANTS = {
  MIN_PASSWORD_LENGTH: 8,
  MAX_USERNAME_LENGTH: 50,
  MIN_USERNAME_LENGTH: 3,
  MAX_TITLE_LENGTH: 200,
  MAX_DESCRIPTION_LENGTH: 2000,
} as const;
