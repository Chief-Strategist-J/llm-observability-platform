'use client';

import React, { Suspense } from 'react';
import { Clock, Zap, AlertTriangle, Activity, Server, Cpu } from 'lucide-react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { EmptyState } from '../../../components/states/EmptyState';
import { useLatencyDashboardData } from '@/features/latency/hooks';

function LatencyDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();
  const { percentiles, slo, attribution, baseline, loading, error } = useLatencyDashboardData(filters);

  const hasData = percentiles !== null || slo !== null || attribution !== null || baseline.length > 0;

  return (
    <div className="flex flex-col gap-6">
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {!loading && !hasData && !error && (
        <EmptyState
          title="No Latency Telemetry Found"
          description={`No telemetry data recorded for ${filters.timeRange} | Model: ${filters.model || 'All'} | Service: ${filters.service || 'All'}`}
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>P50 Latency (Median)</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold">{loading ? "..." : percentiles ? `${percentiles.p50} ms` : "-"}</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>P95 Latency Ribbon</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold">{loading ? "..." : percentiles ? `${percentiles.p95} ms` : "-"}</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>P99 Tail Latency</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-bold">{loading ? "..." : percentiles ? `${percentiles.p99} ms` : "-"}</div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">
            Samples: {percentiles ? percentiles.sample_count : 0}
          </div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>SLO Budget Remaining</span>
            <Activity className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold">{loading ? "..." : slo ? `${slo.budget_remaining_pct}%` : "-"}</div>
          {slo && <div className="text-xs text-emerald-500">Threshold: {slo.slo_threshold_ms} ms</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Server className="w-4 h-4 text-primary" />
            <span>Latency Segment Attribution Breakdown</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-3 rounded-lg bg-[hsl(var(--muted)/0.3)] border border-[hsl(var(--border))]">
              <span className="text-[hsl(var(--muted-foreground))]">DNS Resolution</span>
              <div className="text-lg font-bold mt-1">{attribution ? `${attribution.dns} ms` : "-"}</div>
            </div>
            <div className="p-3 rounded-lg bg-[hsl(var(--muted)/0.3)] border border-[hsl(var(--border))]">
              <span className="text-[hsl(var(--muted-foreground))]">TCP Handshake</span>
              <div className="text-lg font-bold mt-1">{attribution ? `${attribution.tcp} ms` : "-"}</div>
            </div>
            <div className="p-3 rounded-lg bg-[hsl(var(--muted)/0.3)] border border-[hsl(var(--border))]">
              <span className="text-[hsl(var(--muted-foreground))]">Queueing Delay</span>
              <div className="text-lg font-bold mt-1">{attribution ? `${attribution.queue} ms` : "-"}</div>
            </div>
            <div className="p-3 rounded-lg bg-[hsl(var(--muted)/0.3)] border border-[hsl(var(--border))]">
              <span className="text-[hsl(var(--muted-foreground))]">LLM Model Inference</span>
              <div className="text-lg font-bold mt-1 text-primary">{attribution ? `${attribution.inference} ms` : "-"}</div>
            </div>
          </div>
        </div>

        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Cpu className="w-4 h-4 text-primary" />
            <span>7-Day Historical Latency Baseline (P99)</span>
          </div>
          <div className="overflow-x-auto">
            {baseline.length === 0 ? (
              <div className="text-xs text-[hsl(var(--muted-foreground))] py-4">No historical baseline points available</div>
            ) : (
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                    <th className="py-2">Date</th>
                    <th className="py-2">P99 TTFT (ms)</th>
                    <th className="py-2">P99 Total Latency (ms)</th>
                  </tr>
                </thead>
                <tbody>
                  {baseline.map((pt) => (
                    <tr key={pt.date} className="border-b border-[hsl(var(--border)/0.5)]">
                      <td className="py-2 font-medium">{pt.date}</td>
                      <td className="py-2">{pt.p99_ttft_ms} ms</td>
                      <td className="py-2 font-semibold text-primary">{pt.p99_total_ms} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LatencyDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Latency Analytics</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Monitor P50, P95, P99 percentile latency ribbons and TTFT (time-to-first-token).
        </p>
      </div>

      <Suspense fallback={<div className="h-10 animate-pulse bg-muted rounded" />}>
        <LatencyDashboardContent />
      </Suspense>
    </div>
  );
}
