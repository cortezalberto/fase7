/**
 * Git Analytics Dashboard - Métricas de commits y colaboración
 */
// FIX 2.2 & 7.1: Use proper service pattern and add useCallback (Cortez2 audit)
import { useState, useEffect, useCallback } from 'react';
import { gitService } from '@/services/api';
import { useToast } from '@/shared/components/Toast/Toast';
import './GitAnalytics.css';

interface CommitMetrics {
  total_commits: number;
  avg_commits_per_day: number;
  total_insertions: number;
  total_deletions: number;
  code_churn: number;
  avg_commit_size: number;
  refactoring_ratio: number;
}

interface Contributor {
  name: string;
  email: string;
  commits: number;
  insertions: number;
  deletions: number;
  percentage: number;
}

interface CommitTrend {
  date: string;
  commits: number;
  insertions: number;
  deletions: number;
}

interface GitAnalyticsData {
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

type Period = '7d' | '30d' | '90d' | '1y';

const PERIOD_LABELS: Record<Period, string> = {
  '7d': 'Última Semana',
  '30d': 'Último Mes',
  '90d': 'Últimos 3 Meses',
  '1y': 'Último Año'
};

// FIX Cortez48: Use function component pattern instead of React.FC
export function GitAnalytics() {
  const [data, setData] = useState<GitAnalyticsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [period, setPeriod] = useState<Period>('30d');
  const { showToast } = useToast();

  // FIX 7.1: Use useCallback for stable reference (Cortez2 audit)
  // FIX Cortez48: Added AbortController support for cleanup
  const loadAnalytics = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);

    try {
      // FIX 2.2: Use gitService instead of httpClient directly
      const response = await gitService.getAnalytics(period);

      // FIX Cortez48: Check if aborted before updating state
      if (signal?.aborted) return;

      setData(response);
    } catch (error: unknown) {
      // FIX Cortez48: Ignore abort errors
      if (error instanceof Error && error.name === 'AbortError') return;
      if (signal?.aborted) return;

      const errorMessage = error instanceof Error ? error.message : 'Error desconocido';
      showToast(`Error cargando analytics: ${errorMessage}`, 'error');
      setData(null);
    } finally {
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, [period, showToast]);

  // FIX Cortez48: Add AbortController for cleanup on unmount
  useEffect(() => {
    const abortController = new AbortController();
    loadAnalytics(abortController.signal);

    return () => {
      abortController.abort();
    };
  }, [loadAnalytics]);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  return (
    <div className="git-analytics">
      <div className="analytics-header">
        <div>
          <h1>📊 Git Analytics</h1>
          <p>Métricas de commits, colaboración y calidad de código</p>
        </div>

        <div className="period-selector">
          {(Object.keys(PERIOD_LABELS) as Period[]).map((p) => (
            <button
              key={p}
              className={`period-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {PERIOD_LABELS[p]}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analizando repositorio...</p>
        </div>
      )}

      {!loading && !data && (
        <div className="empty-state-large">
          <div className="empty-icon">📊</div>
          <p>No se pudieron cargar las métricas del repositorio</p>
          <button onClick={() => loadAnalytics()}>🔄 Reintentar</button>
        </div>
      )}

      {!loading && data && (
        <div className="analytics-content">
          {/* Repository Info */}
          <div className="repo-info">
            <div className="info-item">
              <span className="info-icon">📁</span>
              <div>
                <div className="info-label">Repositorio</div>
                <div className="info-value">{data.repository}</div>
              </div>
            </div>
            <div className="info-item">
              <span className="info-icon">🌿</span>
              <div>
                <div className="info-label">Branch</div>
                <div className="info-value">{data.branch}</div>
              </div>
            </div>
            <div className="info-item">
              <span className="info-icon">📅</span>
              <div>
                <div className="info-label">Período</div>
                <div className="info-value">
                  {new Date(data.period.start).toLocaleDateString()} -{' '}
                  {new Date(data.period.end).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>

          {/* Commit Metrics */}
          <div className="metrics-section">
            <h2>📈 Métricas de Commits</h2>
            <div className="metrics-grid">
              <MetricCard
                icon="💾"
                label="Total Commits"
                value={data.metrics.total_commits}
                color="#3b82f6"
              />
              <MetricCard
                icon="📊"
                label="Commits/Día"
                value={data.metrics.avg_commits_per_day.toFixed(1)}
                color="#10b981"
              />
              <MetricCard
                icon="➕"
                label="Inserciones"
                value={formatNumber(data.metrics.total_insertions)}
                color="#8b5cf6"
                subtitle={`${formatNumber(data.metrics.total_insertions)} líneas`}
              />
              <MetricCard
                icon="➖"
                label="Eliminaciones"
                value={formatNumber(data.metrics.total_deletions)}
                color="#ef4444"
                subtitle={`${formatNumber(data.metrics.total_deletions)} líneas`}
              />
              <MetricCard
                icon="🔄"
                label="Code Churn"
                value={formatNumber(data.metrics.code_churn)}
                color="#f59e0b"
                subtitle="Cambios totales"
              />
              <MetricCard
                icon="📏"
                label="Tamaño Promedio"
                value={data.metrics.avg_commit_size.toFixed(0)}
                color="#06b6d4"
                subtitle="líneas/commit"
              />
            </div>
          </div>

          {/* Quality Indicators */}
          <div className="quality-section">
            <h2>✅ Indicadores de Calidad</h2>
            <div className="quality-grid">
              <QualityIndicator
                label="Calidad de Mensajes"
                score={data.quality_indicators.message_quality_score}
                maxScore={100}
                icon="📝"
              />
              <QualityIndicator
                label="Conventional Commits"
                score={data.quality_indicators.conventional_commits_ratio * 100}
                maxScore={100}
                icon="🏷️"
              />
              <QualityIndicator
                label="Ratio de Refactoring"
                score={data.metrics.refactoring_ratio * 100}
                maxScore={100}
                icon="♻️"
              />
            </div>

            <div className="quality-detail">
              <div className="detail-item">
                <span className="detail-icon">📏</span>
                <div>
                  <div className="detail-label">Long. Promedio de Mensajes</div>
                  <div className="detail-value">
                    {data.quality_indicators.avg_message_length} caracteres
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Contributors */}
          <div className="contributors-section">
            <h2>👥 Contribuidores</h2>
            <div className="contributors-list">
              {/* FIX Cortez48: Use email as key instead of index */}
              {data.contributors.map((contributor, idx) => (
                <div key={contributor.email} className="contributor-card">
                  <div className="contributor-header">
                    <div className="contributor-avatar">{contributor.name.charAt(0).toUpperCase()}</div>
                    <div className="contributor-info">
                      <div className="contributor-name">{contributor.name}</div>
                      <div className="contributor-email">{contributor.email}</div>
                    </div>
                    <div className="contributor-percentage">{contributor.percentage.toFixed(1)}%</div>
                  </div>

                  <div className="contributor-stats">
                    <div className="stat">
                      <div className="stat-label">Commits</div>
                      <div className="stat-value">{contributor.commits}</div>
                    </div>
                    <div className="stat">
                      <div className="stat-label">Inserciones</div>
                      <div className="stat-value">+{formatNumber(contributor.insertions)}</div>
                    </div>
                    <div className="stat">
                      <div className="stat-label">Eliminaciones</div>
                      <div className="stat-value">-{formatNumber(contributor.deletions)}</div>
                    </div>
                  </div>

                  <div className="contributor-bar">
                    <div
                      className="contributor-bar-fill"
                      style={{
                        width: `${contributor.percentage}%`,
                        backgroundColor: `hsl(${220 - idx * 40}, 70%, 50%)`
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trends Chart */}
          <div className="trends-section">
            <h2>📈 Tendencias de Commits</h2>
            <div className="trends-chart">
              {data.trends.map((trend) => {
                // FIX CRIT-001 Cortez77: Guardia contra división por cero
                const commits = data.trends.map((t) => t.commits);
                const maxCommits = commits.length > 0 ? Math.max(...commits, 1) : 1;
                const height = (trend.commits / maxCommits) * 100;

                {/* FIX Cortez48: Use date as key instead of index */}
                return (
                  <div key={trend.date} className="trend-bar-container">
                    <div className="trend-bar" style={{ height: `${height}%` }}>
                      <div className="trend-value">{trend.commits}</div>
                    </div>
                    <div className="trend-label">{new Date(trend.date).toLocaleDateString('es', { month: 'short', day: 'numeric' })}</div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// FIX Cortez48: Use function component pattern
interface MetricCardProps {
  icon: string;
  label: string;
  value: string | number;
  color: string;
  subtitle?: string;
}

function MetricCard({ icon, label, value, color, subtitle }: MetricCardProps) {
  return (
    <div className="metric-card" style={{ borderColor: color }}>
      <div className="metric-icon" style={{ backgroundColor: `${color}20`, color }}>
        {icon}
      </div>
      <div className="metric-content">
        <div className="metric-label">{label}</div>
        <div className="metric-value" style={{ color }}>
          {value}
        </div>
        {subtitle && <div className="metric-subtitle">{subtitle}</div>}
      </div>
    </div>
  );
};

// FIX Cortez48: Use function component pattern
interface QualityIndicatorProps {
  label: string;
  score: number;
  maxScore: number;
  icon: string;
}

function QualityIndicator({ label, score, maxScore, icon }: QualityIndicatorProps) {
  const percentage = (score / maxScore) * 100;
  const getColor = (): string => {
    if (percentage >= 80) return '#10b981';
    if (percentage >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="quality-indicator">
      <div className="quality-header">
        <span className="quality-icon">{icon}</span>
        <span className="quality-label">{label}</span>
      </div>
      <div className="quality-score" style={{ color: getColor() }}>
        {score.toFixed(1)}
        <span className="quality-max">/{maxScore}</span>
      </div>
      <div className="quality-bar">
        <div
          className="quality-bar-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: getColor()
          }}
        ></div>
      </div>
    </div>
  );
};
