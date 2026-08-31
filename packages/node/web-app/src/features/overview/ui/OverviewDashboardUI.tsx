'use client';

import React from 'react';
import { Activity, Clock, Award, DollarSign, ShieldCheck, AlertTriangle, ArrowUpRight, ArrowDownRight, Layers } from 'lucide-react';
import type { OverviewKPIAggregates, SystemHealthSLOBanner, RecentTracePreview } from '../types';

export interface OverviewDashboardUIProps {
  kpi: OverviewKPIAggregates | null;
  health: SystemHealthSLOBanner | null;
  recentTraces: RecentTracePreview[];
  loading?: boolean;
  error?: string | null;
}

export function OverviewDashboardUI({
  kpi,
  health,
  recentTraces,
  loading = false,
  error = null,
}: OverviewDashboardUIProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-6" role="status" aria-label="Loading overview metrics">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-3 animate-pulse">
              <div className="h-3 w-1/2 rounded bg-[hsl(var(--muted))]" />
              <div className="h-8 w-3/4 rounded bg-[hsl(var(--muted))]" />
              <div className="h-3 w-1/3 rounded bg-[hsl(var(--muted))]" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const isHealthy = !health || health.status === 'healthy';

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {/* Health Banner */}
      <div className={`p-4 rounded-xl border flex items-center justify-between shadow-sm ${
        isHealthy ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
      }`}>
        <div className="flex items-center gap-3">
          {isHealthy ? <ShieldCheck className="w-5 h-5 text-emerald-400" /> : <AlertTriangle className="w-5 h-5 text-amber-400" />}
          <div>
            <div className="font-semibold text-sm">
              {isHealthy ? "System Health & Error Budget Normal" : "SLO Burn Rate Alert Triggered"}
            </div>
            <div className="text-xs opacity-90">
              {health ? health.message : "Telemetry engines operating within SLA parameters."}
            </div>
          </div>
        </div>
        <span className="text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-1 rounded bg-[hsl(var(--card))] border border-[hsl(var(--border))]">
          {isHealthy ? "SLO Status: OK" : "SLO Status: Warning"}
        </span>
      </div>

      {/* KPI Aggregate Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>P95 Latency</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{kpi ? `${kpi.p95_latency_ms} ms` : "-"}</div>
          {kpi && (
            <div className="flex items-center gap-1 text-xs text-emerald-400">
              <ArrowDownRight className="w-3.5 h-3.5" />
              <span>{Math.abs(kpi.p95_latency_delta_pct)}% vs yesterday</span>
            </div>
          )}
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Quality Score Avg</span>
            <Award className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">{kpi ? kpi.quality_avg_score.toFixed(2) : "-"}</div>
          {kpi && (
            <div className="flex items-center gap-1 text-xs text-emerald-400">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>+{kpi.quality_delta_pct}% evaluation score</span>
            </div>
          )}
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Total 24h Spend</span>
            <DollarSign className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-400">{kpi ? `$${kpi.total_spend_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "-"}</div>
          {kpi && (
            <div className="flex items-center gap-1 text-xs text-[hsl(var(--muted-foreground))]">
              <span>+{kpi.spend_delta_pct}% monthly pace</span>
            </div>
          )}
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Active Traced Spans</span>
            <Activity className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold">{kpi ? kpi.active_spans_count.toLocaleString() : "-"}</div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">Live OpenTelemetry streams</div>
        </div>
      </div>

      {/* Recent Traces Table */}
      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Layers className="w-4 h-4 text-primary" />
            <span>Recent Traced Spans</span>
          </div>
          <span className="text-[10px] uppercase font-bold text-[hsl(var(--muted-foreground))]">Live Feed</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                <th className="py-2">Span ID</th>
                <th className="py-2">Operation</th>
                <th className="py-2">Service</th>
                <th className="py-2">Model</th>
                <th className="py-2">Duration</th>
                <th className="py-2">Cost (USD)</th>
                <th className="py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {recentTraces.map((trc) => (
                <tr key={trc.id} className="border-b border-[hsl(var(--border)/0.5)]">
                  <td className="py-2 font-mono font-medium text-primary">{trc.id}</td>
                  <td className="py-2 font-medium">{trc.span_name}</td>
                  <td className="py-2 text-[hsl(var(--muted-foreground))]">{trc.service}</td>
                  <td className="py-2 font-mono">{trc.model}</td>
                  <td className="py-2">{trc.duration_ms} ms</td>
                  <td className="py-2 font-mono">${trc.cost_usd.toFixed(4)}</td>
                  <td className="py-2">
                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                      trc.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    }`}>
                      {trc.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
