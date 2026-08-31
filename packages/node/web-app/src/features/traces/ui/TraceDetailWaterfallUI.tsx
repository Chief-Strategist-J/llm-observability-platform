'use client';

import React from 'react';
import { Layers, Clock, Cpu, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import type { TraceDetailResult, SpanNode } from '../types';

export interface TraceDetailWaterfallUIProps {
  trace: TraceDetailResult | null;
  loading?: boolean;
  error?: string | null;
}

export function TraceDetailWaterfallUI({
  trace,
  loading = false,
  error = null,
}: TraceDetailWaterfallUIProps) {
  if (loading) {
    return (
      <div className="p-6 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-[hsl(var(--muted))] rounded" />
        <div className="h-40 w-full bg-[hsl(var(--muted)/0.3)] rounded" />
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="p-6 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm text-center flex flex-col items-center gap-3">
        <div className="text-sm font-semibold text-rose-400">
          {error || "Trace detail not found or telemetry stream unavailable."}
        </div>
        <Link href="/traces" className="text-xs text-primary hover:underline flex items-center gap-1">
          <ArrowLeft size={14} />
          <span>Return to Trace Explorer</span>
        </Link>
      </div>
    );
  }

  const renderSpanRow = (span: SpanNode, depth = 0) => {
    const leftPct = Math.min(100, Math.max(0, (span.start_time_offset_ms / trace.total_duration_ms) * 100));
    const widthPct = Math.min(100 - leftPct, Math.max(2, (span.duration_ms / trace.total_duration_ms) * 100));

    return (
      <React.Fragment key={span.id}>
        <div className="grid grid-cols-12 items-center py-2 px-3 border-b border-[hsl(var(--border)/0.4)] hover:bg-[hsl(var(--muted)/0.2)] text-xs">
          <div className="col-span-4 flex items-center gap-2 truncate" style={{ paddingLeft: `${depth * 16}px` }}>
            <Layers className="w-3.5 h-3.5 text-primary flex-shrink-0" />
            <span className="font-semibold truncate">{span.name}</span>
            <span className="font-mono text-[10px] text-[hsl(var(--muted-foreground))]">({span.service})</span>
          </div>

          <div className="col-span-2 font-mono text-[10px] text-[hsl(var(--muted-foreground))]">
            {span.id}
          </div>

          <div className="col-span-1 font-mono">
            {span.duration_ms} ms
          </div>

          <div className="col-span-5 relative h-4 bg-[hsl(var(--muted)/0.3)] rounded overflow-hidden">
            <div
              className={`absolute top-0 bottom-0 rounded ${
                span.status === 'error' ? 'bg-rose-500' : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500'
              }`}
              style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
            />
          </div>
        </div>

        {span.children?.map((child) => renderSpanRow(child, depth + 1))}
      </React.Fragment>
    );
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <Link href="/traces" className="text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] flex items-center gap-1">
          <ArrowLeft size={14} />
          <span>Back to Traces List</span>
        </Link>
        <span className="font-mono text-xs text-[hsl(var(--muted-foreground))]">Trace ID: {trace.trace_id}</span>
      </div>

      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        <div className="flex items-center justify-between border-b border-[hsl(var(--border))] pb-3">
          <div>
            <h2 className="text-lg font-bold">{trace.root_span_name}</h2>
            <div className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-3 mt-1">
              <span className="flex items-center gap-1"><Clock size={12} /> Total Duration: {trace.total_duration_ms} ms</span>
              <span className="flex items-center gap-1"><Cpu size={12} /> Spans: {trace.spans.length}</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-[hsl(var(--border))] overflow-hidden bg-[hsl(var(--card))]">
          <div className="grid grid-cols-12 py-2 px-3 bg-[hsl(var(--muted)/0.4)] border-b border-[hsl(var(--border))] text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
            <div className="col-span-4">Span Name & Service</div>
            <div className="col-span-2">Span ID</div>
            <div className="col-span-1">Duration</div>
            <div className="col-span-5">Execution Timeline Waterfall</div>
          </div>

          {trace.spans.map((s) => renderSpanRow(s, 0))}
        </div>
      </div>
    </div>
  );
}
