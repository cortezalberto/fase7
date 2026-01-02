/**
 * Dashboard principal con métricas en tiempo real
 * FIX Cortez31: Removed unused AppContext - use Zustand stores when needed
 */
import React, { useState, useEffect, useRef } from 'react';
import { httpClient } from '@/core/http/HttpClient';
import { wsService } from '@/core/websocket/WebSocketService';
import './Dashboard.css';

interface DashboardMetrics {
  active_sessions: number;
  total_interactions: number;
  avg_cognitive_score: number;
  risk_alerts: number;
  cache_hit_rate: number;
  llm_avg_latency: number;
}

// FIX Cortez48: Use function component pattern instead of React.FC
export function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetrics>({
    active_sessions: 0,
    total_interactions: 0,
    avg_cognitive_score: 0,
    risk_alerts: 0,
    cache_hit_rate: 0,
    llm_avg_latency: 0
  });
  const [loading, setLoading] = useState(true);
  // FIX Cortez30: Add isMounted ref for async operations
  const isMountedRef = useRef<boolean>(true);

  useEffect(() => {
    isMountedRef.current = true;
    loadMetrics();

    // Subscribe to real-time updates via WebSocket
    const unsubscribe = wsService.on('metrics_update', (message) => {
      if (isMountedRef.current) {
        setMetrics(message.data as DashboardMetrics);
      }
    });

    // Poll metrics every 10 seconds
    const interval = setInterval(loadMetrics, 10000);

    // FIX Cortez30: Mark as unmounted on cleanup
    return () => {
      isMountedRef.current = false;
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await httpClient.get<DashboardMetrics>('/metrics/dashboard');
      // FIX Cortez30: Check if component is still mounted before state updates
      if (isMountedRef.current) {
        setMetrics(data);
      }
    } catch (error) {
      console.error('Error loading metrics:', error);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="spinner-large"></div>
        <p>Cargando métricas...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Dashboard General</h1>
        <p>Resumen ejecutivo del sistema AI-Native</p>
      </div>

      <div className="metrics-grid">
        <MetricCard
          title="Sesiones Activas"
          value={metrics.active_sessions}
          icon="🔄"
          color="#3b82f6"
        />

        <MetricCard
          title="Interacciones Totales"
          value={metrics.total_interactions}
          icon="💬"
          color="#10b981"
        />

        <MetricCard
          title="Score Cognitivo Promedio"
          value={`${metrics.avg_cognitive_score.toFixed(1)}/100`}
          icon="🧠"
          color="#8b5cf6"
        />

        <MetricCard
          title="Alertas de Riesgo"
          value={metrics.risk_alerts}
          icon="⚠️"
          color="#ef4444"
          highlight={metrics.risk_alerts > 5}
        />

        <MetricCard
          title="Cache Hit Rate"
          value={`${(metrics.cache_hit_rate * 100).toFixed(1)}%`}
          icon="⚡"
          color="#f59e0b"
        />

        <MetricCard
          title="Latencia LLM"
          value={`${metrics.llm_avg_latency.toFixed(2)}s`}
          icon="⏱️"
          color="#06b6d4"
        />
      </div>

      <div className="quick-actions">
        <h2>Acciones Rápidas</h2>
        <div className="actions-grid">
          <QuickActionCard
            title="Nueva Sesión Tutorial"
            description="Inicia una sesión con el Tutor Cognitivo"
            icon="🎓"
            href="/tutor"
          />

          <QuickActionCard
            title="Ver Evaluaciones"
            description="Analiza el proceso cognitivo de tus estudiantes"
            icon="📊"
            href="/evaluator"
          />

          <QuickActionCard
            title="Simuladores"
            description="Practica con roles profesionales"
            icon="🎭"
            href="/simulator"
          />

          <QuickActionCard
            title="Análisis de Riesgos"
            description="Revisa dependencias y riesgos cognitivos"
            icon="⚠️"
            href="/risks"
          />
        </div>
      </div>
    </div>
  );
};

// FIX Cortez48: Use function component pattern instead of React.FC
interface MetricCardProps {
  title: string;
  value: string | number;
  icon: string;
  color: string;
  highlight?: boolean;
}

function MetricCard({ title, value, icon, color, highlight = false }: MetricCardProps) {
  return (
  <div className={`metric-card ${highlight ? 'highlight' : ''}`}>
    <div className="metric-icon" style={{ backgroundColor: `${color}20`, color }}>
      {icon}
    </div>
    <div className="metric-content">
      <div className="metric-value" style={{ color }}>
        {value}
      </div>
      <div className="metric-title">{title}</div>
    </div>
  </div>
  );
}

// FIX Cortez48: Use function component pattern instead of React.FC
interface QuickActionCardProps {
  title: string;
  description: string;
  icon: string;
  href: string;
}

function QuickActionCard({ title, description, icon, href }: QuickActionCardProps) {
  return (
  <a href={href} className="quick-action-card">
    <div className="action-icon">{icon}</div>
    <div className="action-content">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
    <div className="action-arrow">→</div>
  </a>
  );
}
