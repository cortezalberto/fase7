/**
 * API Types - Re-exports from domain-specific type modules
 *
 * Cortez43: Refactored from monolithic file (893 lines) into 11 domain-specific modules
 *
 * This file maintains backward compatibility by re-exporting all types from
 * the new modular structure in src/types/domain/
 *
 * New imports (recommended):
 *   import { SessionMode, Risk } from '@/types/domain';
 *
 * Legacy imports (still work):
 *   import { SessionMode, Risk } from '@/types/api.types';
 */

// Re-export everything from domain modules
export * from './domain';
