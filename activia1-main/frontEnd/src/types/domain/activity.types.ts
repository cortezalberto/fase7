/**
 * Activity Types - Activity-related interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

import { ActivityDifficulty, HelpLevel } from './enums';

// ==================== POLICY CONFIG ====================

export interface PolicyConfig {
  max_help_level: HelpLevel;
  block_complete_solutions: boolean;
  require_justification: boolean;
  allow_code_snippets: boolean;
  risk_thresholds: Record<string, number>;
}

// ==================== ACTIVITY ====================

export interface ActivityCreate {
  activity_id: string;
  title: string;
  instructions: string;
  teacher_id: string;
  policies: PolicyConfig;
  description?: string;
  evaluation_criteria?: string[];
  subject?: string;
  difficulty?: ActivityDifficulty;
  estimated_duration_minutes?: number;
  tags?: string[];
}

export interface ActivityUpdate {
  title?: string;
  description?: string;
  instructions?: string;
  policies?: PolicyConfig;
  evaluation_criteria?: string[];
  subject?: string;
  difficulty?: ActivityDifficulty;
  estimated_duration_minutes?: number;
  tags?: string[];
}

export interface ActivityResponse {
  id: string;
  activity_id: string;
  title: string;
  description: string | null;
  instructions: string;
  evaluation_criteria: string[];
  teacher_id: string;
  policies: PolicyConfig;
  subject: string | null;
  difficulty: string | null;
  estimated_duration_minutes: number | null;
  tags: string[];
  status: string;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}
