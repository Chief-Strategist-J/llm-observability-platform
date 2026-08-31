'use client';

import React from 'react';
import { Award, TrendingUp, AlertOctagon, ShieldAlert, Cpu, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import type {
  QualitySummaryResult,
  QualityTrendPoint,
  ModelQualityBreakdown,
  FlaggedContentAlert,
} from '../types';

export interface QualityDashboardUIProps {
  summary: QualitySummaryResult | null;
  trend: QualityTrendPoint[];
  models: ModelQualityBreakdown[];
  flaggedAlerts: FlaggedContentAlert[];
  loading?: boolean;
  error?: string | null;
}

export function QualityDashboardUI({
  summary,
  trend,
  models,
  flaggedAlerts,
  loading = false,
  error = null,
}: QualityDashboardUIProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-6" role="status" aria-label="Loading quality evaluation metrics">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-3 animate-pulse"
            >
              <div className="h-3 w-1/2 rounded bg-[hsl(var(--muted))]" />
              <div className="h-8 w-3/4 rounded bg-[hsl(var(--muted))]" />
              <div className="h-3 w-1/3 rounded bg-[hsl(var(--muted))]" />
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4 animate-pulse">
            <div className="h-4 w-1/3 rounded bg-[hsl(var(--muted))]" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-10 w-full rounded bg-[hsl(var(--muted)/0.3)]" />
              ))}
            </div>
          </div>

          <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4 animate-pulse">
            <div className="h-4 w-1/3 rounded bg-[hsl(var(--muted))]" />
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-12 w-full rounded bg-[hsl(var(--muted)/0.3)]" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {/* 1. Summary KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Average Quality Score</span>
            <Award className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {summary ? summary.avg_quality_score.toFixed(2) : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">
            Target threshold: &ge; 0.85
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Score Delta %</span>
            <TrendingUp className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="text-2xl font-bold text-cyan-400">
            {summary ? `${summary.score_delta_pct >= 0 ? '+' : ''}${summary.score_delta_pct}%` : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">
            vs 7-day rolling baseline
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Below SLO Threshold</span>
            <AlertOctagon className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {summary ? summary.below_slo_count : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">
            Evaluations needing review
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Total Evaluated Prompts</span>
            <CheckCircle2 className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold">
            {summary ? summary.total_evaluated_prompts.toLocaleString() : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">
            Live telemetry coverage
          </div>
        </div>
      </div>

      {/* 2. Main Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Model Quality Breakdown */}
        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Cpu className="w-4 h-4 text-primary" />
            <span>Model Quality Score Distribution</span>
          </div>

          <div className="overflow-x-auto">
            {models.length === 0 ? (
              <div className="text-xs text-[hsl(var(--muted-foreground))] py-4">No model evaluation data available</div>
            ) : (
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                    <th className="py-2">Model</th>
                    <th className="py-2">Avg Score</th>
                    <th className="py-2">Min / Max</th>
                    <th className="py-2">Pass Rate</th>
                    <th className="py-2">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {models.map((m) => (
                    <tr key={m.model} className="border-b border-[hsl(var(--border)/0.5)]">
                      <td className="py-2.5 font-medium font-mono text-[hsl(var(--foreground))]">{m.model}</td>
                      <td className="py-2.5 font-semibold text-emerald-400">{m.avg_score.toFixed(2)}</td>
                      <td className="py-2.5 text-[hsl(var(--muted-foreground))]">{m.min_score.toFixed(2)} / {m.max_score.toFixed(2)}</td>
                      <td className="py-2.5">
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          {m.pass_rate_pct}%
                        </span>
                      </td>
                      <td className="py-2.5">{m.evaluation_count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Flagged Content & Toxicity Alerts */}
        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <ShieldAlert className="w-4 h-4 text-rose-500" />
              <span>Flagged Content Alerts</span>
            </div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
              {flaggedAlerts.length} Active Alerts
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {flaggedAlerts.length === 0 ? (
              <div className="text-xs text-[hsl(var(--muted-foreground))] py-4">No content policy or quality alerts</div>
            ) : (
              flaggedAlerts.map((alert) => {
                const isCritical = alert.severity === 'critical';
                const isWarning = alert.severity === 'warning';
                return (
                  <div
                    key={alert.id}
                    className="p-3 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--muted)/0.2)] flex flex-col gap-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {isCritical ? (
                          <AlertOctagon className="w-3.5 h-3.5 text-rose-500" />
                        ) : isWarning ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
                        ) : (
                          <Info className="w-3.5 h-3.5 text-cyan-500" />
                        )}
                        <span className="font-semibold uppercase tracking-wide text-[10px] text-[hsl(var(--foreground))]">
                          {alert.alert_type.replace('_', ' ')}
                        </span>
                      </div>
                      <span className="font-mono text-[10px] text-[hsl(var(--muted-foreground))]">
                        Confidence: {(alert.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    <p className="text-[hsl(var(--muted-foreground))] line-clamp-2 leading-relaxed">
                      &ldquo;{alert.prompt_snippet}&rdquo;
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-[hsl(var(--muted-foreground))] pt-1 border-t border-[hsl(var(--border)/0.4)]">
                      <span className="font-mono">{alert.span_id}</span>
                      <span>{new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* 3. Rolling Quality Score Trend Table */}
      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <TrendingUp className="w-4 h-4 text-cyan-500" />
          <span>7-Day Rolling Quality & Policy Alert Trend</span>
        </div>

        <div className="overflow-x-auto">
          {trend.length === 0 ? (
            <div className="text-xs text-[hsl(var(--muted-foreground))] py-4">No trend historical points available</div>
          ) : (
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                  <th className="py-2">Date</th>
                  <th className="py-2">Average Quality Score</th>
                  <th className="py-2">Toxicity Alerts</th>
                  <th className="py-2">Hallucination Alerts</th>
                </tr>
              </thead>
              <tbody>
                {trend.map((pt) => (
                  <tr key={pt.date} className="border-b border-[hsl(var(--border)/0.5)]">
                    <td className="py-2 font-medium font-mono">{pt.date}</td>
                    <td className="py-2 font-bold text-emerald-400">{pt.avg_quality_score.toFixed(2)}</td>
                    <td className="py-2">
                      {pt.toxicity_alerts > 0 ? (
                        <span className="text-rose-400 font-semibold">{pt.toxicity_alerts}</span>
                      ) : (
                        <span className="text-[hsl(var(--muted-foreground))]">0</span>
                      )}
                    </td>
                    <td className="py-2">
                      {pt.hallucination_alerts > 0 ? (
                        <span className="text-amber-400 font-semibold">{pt.hallucination_alerts}</span>
                      ) : (
                        <span className="text-[hsl(var(--muted-foreground))]">0</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
