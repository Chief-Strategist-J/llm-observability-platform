'use client';

import React from 'react';
import Link from 'next/link';
import { Layers, Search, ExternalLink } from 'lucide-react';
import type { TraceSummary } from '../types';

export interface TracesDashboardUIProps {
  traces: TraceSummary[];
  loading?: boolean;
  error?: string | null;
}

export function TracesDashboardUI({
  traces,
  loading = false,
  error = null,
}: TracesDashboardUIProps) {
  if (loading) {
    return (
      <div className="flex flex-col gap-6" role="status" aria-label="Loading traces explorer">
        <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm space-y-4 animate-pulse">
          <div className="h-4 w-1/4 bg-[hsl(var(--muted))] rounded" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-10 w-full bg-[hsl(var(--muted)/0.3)] rounded" />
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

      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Layers className="w-4 h-4 text-primary" />
            <span>Distributed Spans & Execution Traces</span>
          </div>
          <span className="text-[10px] uppercase font-bold text-[hsl(var(--muted-foreground))]">
            {traces.length} Traces Loaded
          </span>
        </div>

        <div className="overflow-x-auto">
          {traces.length === 0 ? (
            <div className="text-xs text-[hsl(var(--muted-foreground))] py-8 text-center flex flex-col items-center gap-2">
              <Search className="w-6 h-6 opacity-40" />
              <span>No distributed traces recorded for the selected filter parameters.</span>
            </div>
          ) : (
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]">
                  <th className="py-2.5">Trace ID</th>
                  <th className="py-2.5">Root Operation</th>
                  <th className="py-2.5">Service</th>
                  <th className="py-2.5">Model</th>
                  <th className="py-2.5">Duration</th>
                  <th className="py-2.5">Total Tokens</th>
                  <th className="py-2.5">Cost</th>
                  <th className="py-2.5">Status</th>
                  <th className="py-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {traces.map((trc) => (
                  <tr key={trc.id} className="border-b border-[hsl(var(--border)/0.5)] hover:bg-[hsl(var(--muted)/0.2)]">
                    <td className="py-2.5 font-mono font-medium text-primary">{trc.id}</td>
                    <td className="py-2.5 font-semibold">{trc.root_span_name}</td>
                    <td className="py-2.5 text-[hsl(var(--muted-foreground))]">{trc.service}</td>
                    <td className="py-2.5 font-mono">{trc.model}</td>
                    <td className="py-2.5">{trc.duration_ms} ms</td>
                    <td className="py-2.5">{trc.total_tokens.toLocaleString()}</td>
                    <td className="py-2.5 font-mono">${trc.cost_usd.toFixed(4)}</td>
                    <td className="py-2.5">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${
                        trc.status === 'success' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                      }`}>
                        {trc.status}
                      </span>
                    </td>
                    <td className="py-2.5 text-right">
                      <Link
                        href={`/traces/${trc.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:underline"
                      >
                        <span>Waterfall</span>
                        <ExternalLink size={12} />
                      </Link>
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
