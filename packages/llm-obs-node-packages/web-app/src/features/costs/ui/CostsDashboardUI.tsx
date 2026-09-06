'use client';

import { DollarSign, TrendingUp, Calendar, PieChart, Cpu } from 'lucide-react';
import type { CostSummaryResult, CostByProvider } from '../types';

export interface CostsDashboardUIProps {
  summary: CostSummaryResult | null;
  providers: CostByProvider[];
  loading?: boolean;
  error?: string | null;
}

export function CostsDashboardUI({
  summary,
  providers,
  loading = false,
  error = null,
}: CostsDashboardUIProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-6" role="status" aria-label="Loading cost analytics">
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

  return (
    <div className="flex flex-col gap-6">
      {error && (
        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500 text-xs font-medium">
          {error}
        </div>
      )}

      {/* KPI Metric Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Total USD Spend</span>
            <DollarSign className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-emerald-400">
            {summary ? `$${summary.total_cost_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">Current billing cycle</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Daily Average Spend</span>
            <Calendar className="w-4 h-4 text-cyan-500" />
          </div>
          <div className="text-2xl font-bold text-cyan-400">
            {summary ? `$${summary.daily_avg_usd.toFixed(2)}` : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">Rolling daily rate</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Pace Delta %</span>
            <TrendingUp className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-400">
            {summary ? `${summary.cost_delta_pct >= 0 ? '+' : ''}${summary.cost_delta_pct}%` : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">vs previous billing period</div>
        </div>

        <div className="p-4 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-2">
          <div className="flex items-center justify-between text-xs text-[hsl(var(--muted-foreground))]">
            <span>Projected Monthly Spend</span>
            <PieChart className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold">
            {summary ? `$${summary.projected_monthly_usd.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : "-"}
          </div>
          <div className="text-xs text-[hsl(var(--muted-foreground))]">Run-rate forecast</div>
        </div>
      </div>

      {/* Provider & Model Spend Table */}
      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Cpu className="w-4 h-4 text-primary" />
            <span>Cost Spend Breakdown by Provider & Model</span>
          </div>
          <span className="text-[10px] uppercase font-bold text-[hsl(var(--muted-foreground))]">
            {providers.length} Models Tracked
          </span>
        </div>

        <div className="overflow-x-auto">
          {providers.length === 0 ? (
            <div className="text-xs text-[hsl(var(--muted-foreground))] py-6 text-center">
              No cost breakdown data available for the active filters.
            </div>
          ) : (
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                  <th className="py-2.5">Provider</th>
                  <th className="py-2.5">Model</th>
                  <th className="py-2.5">Total Spend</th>
                  <th className="py-2.5">Token Consumption</th>
                  <th className="py-2.5">% Share</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((p) => (
                  <tr key={`${p.provider}-${p.model}`} className="border-b border-[hsl(var(--border)/0.5)]">
                    <td className="py-2.5 font-medium">{p.provider}</td>
                    <td className="py-2.5 font-mono font-semibold">{p.model}</td>
                    <td className="py-2.5 font-bold text-emerald-400">${p.cost_usd.toFixed(2)}</td>
                    <td className="py-2.5 font-mono">{p.token_count.toLocaleString()} tokens</td>
                    <td className="py-2.5 font-semibold text-primary">{p.pct_of_total}%</td>
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
