/**
 * Git Types - Git analytics interfaces
 *
 * Cortez43: Extracted from monolithic api.types.ts (893 lines)
 */

// ==================== GIT ANALYTICS ====================

export interface CommitMetrics {
  total_commits: number;
  avg_commits_per_day: number;
  total_insertions: number;
  total_deletions: number;
  code_churn: number;
  avg_commit_size: number;
  refactoring_ratio: number;
}

export interface Contributor {
  name: string;
  email: string;
  commits: number;
  insertions: number;
  deletions: number;
  percentage: number;
}

export interface CommitTrend {
  date: string;
  commits: number;
  insertions: number;
  deletions: number;
}

export interface GitAnalyticsData {
  repository: string;
  branch: string;
  period: {
    start: string;
    end: string;
  };
  metrics: CommitMetrics;
  contributors: Contributor[];
  trends: CommitTrend[];
  quality_indicators: {
    message_quality_score: number;
    avg_message_length: number;
    conventional_commits_ratio: number;
  };
}
