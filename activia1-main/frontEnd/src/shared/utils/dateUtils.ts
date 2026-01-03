/**
 * Date Formatting Utilities
 *
 * FIX Cortez71 LOW-004: Standardized date formatting across the application
 *
 * Usage:
 *   import { formatDate, formatTime, formatDateTime, formatRelative } from '@/shared/utils/dateUtils';
 */

// Default locale for the application
const DEFAULT_LOCALE = 'es-ES';

/**
 * Format a date to a localized date string
 * @example formatDate(new Date()) // "3 ene 2026"
 */
export function formatDate(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short', year: 'numeric' }
): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleDateString(DEFAULT_LOCALE, options);
}

/**
 * Format a date to a localized time string
 * @example formatTime(new Date()) // "14:30"
 */
export function formatTime(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = { hour: '2-digit', minute: '2-digit' }
): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleTimeString(DEFAULT_LOCALE, options);
}

/**
 * Format a date to a full localized date-time string
 * @example formatDateTime(new Date()) // "3 ene 2026, 14:30"
 */
export function formatDateTime(
  date: Date | string | number,
  options: Intl.DateTimeFormatOptions = {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }
): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleString(DEFAULT_LOCALE, options);
}

/**
 * Format a date to ISO string (for API calls)
 * @example formatISO(new Date()) // "2026-01-03T14:30:00.000Z"
 */
export function formatISO(date: Date | string | number): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';
  return d.toISOString();
}

/**
 * Format a date as relative time
 * @example formatRelative(new Date(Date.now() - 60000)) // "hace 1 minuto"
 */
export function formatRelative(date: Date | string | number): string {
  const d = new Date(date);
  if (isNaN(d.getTime())) return '-';

  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSecs < 60) return 'hace unos segundos';
  if (diffMins < 60) return `hace ${diffMins} ${diffMins === 1 ? 'minuto' : 'minutos'}`;
  if (diffHours < 24) return `hace ${diffHours} ${diffHours === 1 ? 'hora' : 'horas'}`;
  if (diffDays < 7) return `hace ${diffDays} ${diffDays === 1 ? 'dia' : 'dias'}`;

  return formatDate(d);
}

/**
 * Format duration in seconds to human-readable string
 * @example formatDuration(3665) // "1h 1m 5s"
 */
export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0s';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  const parts: string[] = [];
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);

  return parts.join(' ');
}

/**
 * Format duration in milliseconds to human-readable string
 * @example formatDurationMs(3665000) // "1h 1m 5s"
 */
export function formatDurationMs(ms: number): string {
  return formatDuration(Math.floor(ms / 1000));
}

/**
 * Check if a date is today
 */
export function isToday(date: Date | string | number): boolean {
  const d = new Date(date);
  const today = new Date();
  return (
    d.getDate() === today.getDate() &&
    d.getMonth() === today.getMonth() &&
    d.getFullYear() === today.getFullYear()
  );
}

/**
 * Get start of day for a given date
 */
export function startOfDay(date: Date | string | number): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

/**
 * Get end of day for a given date
 */
export function endOfDay(date: Date | string | number): Date {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}
