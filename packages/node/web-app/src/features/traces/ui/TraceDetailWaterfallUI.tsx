'use client';

import React, { useState } from 'react';
import { Layers, Clock, Cpu, ArrowLeft, ChevronRight, ChevronDown, Info, ExternalLink } from 'lucide-react';
import Link from 'next/link';
import type { TraceDetailResult, SpanNode } from '../types';
import { SpanAttributeDrawer } from './SpanAttributeDrawer';

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
  const [selectedSpan, setSelectedSpan] = useState<SpanNode | null>(null);
  const [collapsedSpanIds, setCollapsedSpanIds] = useState<Set<string>>(new Set());

  const toggleCollapse = (spanId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setCollapsedSpanIds((prev) => {
      const next = new Set(prev);
      if (next.has(spanId)) {
        next.delete(spanId);
      } else {
        next.add(spanId);
      }
      return next;
    });
  };

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

  // Generate 5 timeline tick marks for the waterfall header
  const ticks = [0, 0.25, 0.5, 0.75, 1.0].map((ratio) => Math.round(ratio * trace.total_duration_ms));

  const renderSpanRow = (span: SpanNode, depth = 0) => {
    const isCollapsed = collapsedSpanIds.has(span.id);
    const hasChildren = span.children && span.children.length > 0;

    const leftPct = Math.min(100, Math.max(0, (span.start_time_offset_ms / trace.total_duration_ms) * 100));
    const widthPct = Math.min(100 - leftPct, Math.max(1.5, (span.duration_ms / trace.total_duration_ms) * 100));

    return (
      <React.Fragment key={span.id}>
        <div
          onClick={() => setSelectedSpan(span)}
          className={`grid grid-cols-12 items-center py-2 px-3 border-b border-[hsl(var(--border)/0.4)] hover:bg-[hsl(var(--muted)/0.3)] transition-colors cursor-pointer text-xs ${
            selectedSpan?.id === span.id ? 'bg-primary/10 border-l-4 border-l-primary' : ''
          }`}
        >
          {/* Span Name & Depth */}
          <div className="col-span-4 flex items-center gap-2 truncate" style={{ paddingLeft: `${depth * 16}px` }}>
            {hasChildren ? (
              <button
                onClick={(e) => toggleCollapse(span.id, e)}
                className="p-0.5 hover:bg-[hsl(var(--muted))] rounded transition-colors text-[hsl(var(--muted-foreground))]"
                aria-label={isCollapsed ? "Expand child spans" : "Collapse child spans"}
              >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
              </button>
            ) : (
              <span className="w-4 h-4 flex-shrink-0" />
            )}

            <Layers className="w-3.5 h-3.5 text-primary flex-shrink-0" />
            <span className="font-semibold truncate text-[hsl(var(--foreground))]" title={span.name}>
              {span.name}
            </span>
            <span className="font-mono text-[10px] text-[hsl(var(--muted-foreground))]">
              ({span.service})
            </span>
          </div>

          {/* Span ID */}
          <div className="col-span-2 font-mono text-[10px] text-[hsl(var(--muted-foreground))] truncate" title={span.id}>
            {span.id}
          </div>

          {/* Duration */}
          <div className="col-span-1 font-mono font-medium text-xs">
            {span.duration_ms} ms
          </div>

          {/* Timeline Bar */}
          <div className="col-span-5 relative h-5 bg-[hsl(var(--muted)/0.25)] rounded overflow-hidden flex items-center">
            <div
              className={`absolute top-0.5 bottom-0.5 rounded shadow-sm transition-all ${
                span.status === 'error'
                  ? 'bg-gradient-to-r from-rose-600 to-red-500'
                  : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-500'
              }`}
              style={{ left: `${leftPct}%`, width: `${widthPct}%` }}
              title={`${span.name}: ${span.duration_ms} ms (${leftPct.toFixed(1)}% start offset)`}
            />
          </div>
        </div>

        {/* Render child spans recursively if not collapsed */}
        {!isCollapsed && hasChildren && span.children!.map((child) => renderSpanRow(child, depth + 1))}
      </React.Fragment>
    );
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Back Button & Top Action */}
      <div className="flex items-center justify-between">
        <Link href="/traces" className="text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] flex items-center gap-1.5 transition-colors">
          <ArrowLeft size={14} />
          <span>Back to Traces Explorer</span>
        </Link>
        <span className="font-mono text-xs text-[hsl(var(--muted-foreground))]">Trace ID: <strong className="text-primary">{trace.trace_id}</strong></span>
      </div>

      {/* Main Flame Graph Container */}
      <div className="p-5 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-sm flex flex-col gap-4">
        {/* Header Summary */}
        <div className="flex items-center justify-between border-b border-[hsl(var(--border))] pb-4">
          <div>
            <h2 className="text-lg font-bold text-[hsl(var(--foreground))] flex items-center gap-2">
              <span>{trace.root_span_name}</span>
            </h2>
            <div className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1.5"><Clock size={13} className="text-blue-500" /> Total Duration: <strong className="text-[hsl(var(--foreground))] font-mono">{trace.total_duration_ms} ms</strong></span>
              <span className="flex items-center gap-1.5"><Cpu size={13} className="text-indigo-500" /> Total Spans: <strong className="text-[hsl(var(--foreground))] font-mono">{trace.spans.length}</strong></span>
            </div>
          </div>

          <div className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-1.5 bg-[hsl(var(--muted)/0.3)] px-3 py-1.5 rounded-lg border border-[hsl(var(--border))]">
            <Info size={13} className="text-primary" />
            <span>Click any span row to inspect OpenTelemetry metadata & payloads</span>
          </div>
        </div>

        {/* Flame Graph Waterfall Grid */}
        <div className="rounded-xl border border-[hsl(var(--border))] overflow-hidden bg-[hsl(var(--card))]">
          {/* Header Row with Timeline Scale Ticks */}
          <div className="grid grid-cols-12 py-2 px-3 bg-[hsl(var(--muted)/0.4)] border-b border-[hsl(var(--border))] text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
            <div className="col-span-4">Span Name & Service</div>
            <div className="col-span-2">Span ID</div>
            <div className="col-span-1">Duration</div>
            <div className="col-span-5 relative flex items-center justify-between px-1 font-mono text-[9px] font-semibold text-[hsl(var(--muted-foreground))]">
              {ticks.map((t, idx) => (
                <span key={idx}>{t} ms</span>
              ))}
            </div>
          </div>

          {/* Span Rows */}
          {trace.spans.map((s) => renderSpanRow(s, 0))}
        </div>
      </div>

      {/* Slide-over Span Attribute Inspection Drawer */}
      <SpanAttributeDrawer
        span={selectedSpan}
        totalTraceDurationMs={trace.total_duration_ms}
        onClose={() => setSelectedSpan(null)}
      />
    </div>
  );
}
