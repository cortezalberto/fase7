/**
 * Feature Flags Configuration
 *
 * FIX Cortez71 MED-008: Centralized feature flag system
 *
 * Usage:
 *   import { featureFlags } from '@/shared/config/featureFlags.config';
 *   if (featureFlags.useV2TrainingEndpoints) { ... }
 *
 * Environment Variables (optional):
 *   VITE_FEATURE_V2_TRAINING=true
 *   VITE_FEATURE_N4_TRACING=true
 *   VITE_FEATURE_RISK_MONITOR=true
 *   VITE_FEATURE_LTI_INTEGRATION=true
 */

// Helper to parse boolean env variables
const parseBoolEnv = (value: string | undefined, defaultValue: boolean): boolean => {
  if (value === undefined) return defaultValue;
  return value.toLowerCase() === 'true' || value === '1';
};

/**
 * Feature flags for the application
 * Defaults are for development; override via environment variables in production
 */
export const featureFlags = {
  // Training V2 endpoints with T-IA-Cog integration
  useV2TrainingEndpoints: parseBoolEnv(
    import.meta.env.VITE_FEATURE_V2_TRAINING,
    false // Default: use V1 endpoints
  ),

  // N4 cognitive traceability tracking
  enableN4Tracing: parseBoolEnv(
    import.meta.env.VITE_FEATURE_N4_TRACING,
    false // Default: disabled
  ),

  // Real-time risk monitoring during training
  enableRiskMonitor: parseBoolEnv(
    import.meta.env.VITE_FEATURE_RISK_MONITOR,
    false // Default: disabled
  ),

  // LTI 1.3 Moodle integration
  enableLTIIntegration: parseBoolEnv(
    import.meta.env.VITE_FEATURE_LTI_INTEGRATION,
    false // Default: disabled
  ),

  // Show development-only features
  showDevFeatures: import.meta.env.DEV,

  // Enable verbose API logging
  enableApiLogging: import.meta.env.DEV,

  // Enable performance metrics collection
  enablePerformanceMetrics: parseBoolEnv(
    import.meta.env.VITE_FEATURE_PERF_METRICS,
    false
  ),

  // Enable cognitive state visualization in UI
  showCognitiveState: parseBoolEnv(
    import.meta.env.VITE_FEATURE_COGNITIVE_UI,
    true // Default: show cognitive state
  ),

  // Enable reflection prompts after exercises
  enableReflectionPrompts: parseBoolEnv(
    import.meta.env.VITE_FEATURE_REFLECTIONS,
    true // Default: enabled
  ),
} as const;

// Type for feature flag keys
export type FeatureFlagKey = keyof typeof featureFlags;

/**
 * Check if a feature is enabled
 */
export function isFeatureEnabled(flag: FeatureFlagKey): boolean {
  return featureFlags[flag];
}

/**
 * Get all enabled features (useful for debugging)
 */
export function getEnabledFeatures(): FeatureFlagKey[] {
  return (Object.keys(featureFlags) as FeatureFlagKey[]).filter(
    (key) => featureFlags[key]
  );
}

export default featureFlags;
