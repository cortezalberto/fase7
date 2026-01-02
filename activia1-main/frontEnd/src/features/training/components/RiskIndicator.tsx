/**
 * RiskIndicator Component - Display active risks during training
 *
 * Cortez55: New component for N4 traceability
 * Shows real-time risk alerts detected by AR-IA
 */

import type { RiskFlag, RiskSeverityEnum, RiskTypeEnum } from '@/services/api';

interface RiskIndicatorProps {
  risks: RiskFlag[];
  className?: string;
}

// Severity colors
const severityColors: Record<RiskSeverityEnum, { bg: string; text: string; border: string }> = {
  low: { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/30' },
  medium: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  high: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  critical: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
};

// Risk type icons
const riskIcons: Record<RiskTypeEnum, string> = {
  copy_paste: 'M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3',
  frustration: 'M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  hint_dependency: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  rapid_submission: 'M13 10V3L4 14h7v7l9-11h-7z',
  time_pressure: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
  cognitive_overload: 'M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z',
};

// Risk type labels
const riskLabels: Record<RiskTypeEnum, string> = {
  copy_paste: 'Posible Copy-Paste',
  frustration: 'Nivel de Frustracion',
  hint_dependency: 'Dependencia de Pistas',
  rapid_submission: 'Envios Rapidos',
  time_pressure: 'Presion de Tiempo',
  cognitive_overload: 'Sobrecarga Cognitiva',
};

export function RiskIndicator({ risks, className = '' }: RiskIndicatorProps) {
  if (risks.length === 0) return null;

  // Filter unresolved risks and sort by severity
  const activeRisks = risks
    .filter((r) => !r.resuelto)
    .sort((a, b) => {
      const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
      return (severityOrder[a.severidad] || 4) - (severityOrder[b.severidad] || 4);
    });

  if (activeRisks.length === 0) return null;

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span>Alertas Detectadas ({activeRisks.length})</span>
      </div>

      {activeRisks.map((risk, index) => {
        const colors = severityColors[risk.severidad] || severityColors.low;
        const icon = riskIcons[risk.tipo] || riskIcons.cognitive_overload;
        const label = riskLabels[risk.tipo] || risk.tipo;

        return (
          <div
            key={`${risk.tipo}-${index}`}
            className={`${colors.bg} ${colors.border} border rounded-lg p-3 flex items-start gap-3 animate-in fade-in slide-in-from-right duration-300`}
          >
            <div className={`${colors.text} flex-shrink-0`}>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className={`${colors.text} font-medium text-sm`}>{label}</span>
                <span
                  className={`${colors.text} text-xs uppercase px-2 py-0.5 rounded-full ${colors.bg}`}
                >
                  {risk.severidad}
                </span>
              </div>
              <p className="text-gray-400 text-xs mt-1 line-clamp-2">{risk.mensaje}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// Compact version for sidebar/header
export function RiskBadge({ risks }: { risks: RiskFlag[] }) {
  const activeRisks = risks.filter((r) => !r.resuelto);
  if (activeRisks.length === 0) return null;

  // Get highest severity
  const hasCritical = activeRisks.some((r) => r.severidad === 'critical');
  const hasHigh = activeRisks.some((r) => r.severidad === 'high');

  const bgColor = hasCritical ? 'bg-red-500' : hasHigh ? 'bg-orange-500' : 'bg-yellow-500';
  const pulseClass = hasCritical || hasHigh ? 'animate-pulse' : '';

  return (
    <div
      className={`${bgColor} ${pulseClass} text-white text-xs font-bold px-2 py-1 rounded-full flex items-center gap-1`}
      title={`${activeRisks.length} alertas activas`}
    >
      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
      <span>{activeRisks.length}</span>
    </div>
  );
}
