'use client';

import React, { useState } from 'react';
import { Layers, Clock, Cpu, ArrowLeft, ChevronRight, ChevronDown, Info } from 'lucide-react';
import Link from 'next/link';
import type { TraceDetailResult, SpanNode } from '../types';
import { SpanAttributeDrawer } from './SpanAttributeDrawer';
import { TRACES_TEXT } from '../constants';

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
      <div className="traces-card-panel animate-pulse space-y-4">
        <div className="h-6 w-1/3 bg-[hsl(var(--muted))] rounded" />
        <div className="h-40 w-full bg-[hsl(var(--muted)/0.3)] rounded" />
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="traces-card-panel text-center flex flex-col items-center gap-3">
        <div className="text-sm font-semibold text-rose-400">
          {error || "Trace detail not found or telemetry stream unavailable."}
        </div>
        <Link href="/traces" className="text-xs text-primary hover:underline flex items-center gap-1">
          <ArrowLeft size={14} />
          <span>{TRACES_TEXT.WATERFALL_BACK_LINK}</span>
        </Link>
      </div>
    );
  }

  const totalDuration = trace.total_duration_ms > 0 ? trace.total_duration_ms : 1;
  const spansList = trace.spans ?? [];

  // Generate 5 timeline tick marks for the waterfall header
  const ticks = [0, 0.25, 0.5, 0.75, 1.0].map((ratio) => Math.round(ratio * totalDuration));

  // Recursive null-safe span node row renderer for arbitrary depth
  const renderSpanRow = (span: SpanNode, depth = 0): React.ReactNode => {
    if (!span) return null;

    const spanId = span.id || `spn_unknown_${Math.random()}`;
    const spanName = span.name || 'Unnamed Span';
    const serviceName = span.service || 'unspecified';
    const durationMs = span.duration_ms ?? 0;
    const startOffsetMs = span.start_time_offset_ms ?? 0;
    const childrenList = Array.isArray(span.children) ? span.children : [];
    const hasChildren = childrenList.length > 0;
    const isCollapsed = collapsedSpanIds.has(spanId);

    const leftPct = Math.min(100, Math.max(0, (startOffsetMs / totalDuration) * 100));
    const widthPct = Math.min(100 - leftPct, Math.max(1.5, (durationMs / totalDuration) * 100));

    return (
      <React.Fragment key={spanId}>
        <div
          onClick={() => setSelectedSpan(span)}
          className={`grid grid-cols-12 items-center py-2 px-3 border-b border-[hsl(var(--border)/0.4)] hover:bg-[hsl(var(--muted)/0.3)] transition-colors cursor-pointer text-xs ${
            selectedSpan?.id === spanId ? 'bg-primary/10 border-l-4 border-l-primary' : ''
          }`}
        >
          {/* Span Name & Depth Indentation */}
          <div className="col-span-4 flex items-center gap-2 truncate" style={{ paddingLeft: `${Math.min(depth * 16, 120)}px` }}>
            {hasChildren ? (
              <button
                onClick={(e) => toggleCollapse(spanId, e)}
                className="p-0.5 hover:bg-[hsl(var(--muted))] rounded transition-colors text-[hsl(var(--muted-foreground))]"
                aria-label={isCollapsed ? "Expand child spans" : "Collapse child spans"}
              >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
              </button>
            ) : (
              <span className="w-4 h-4 flex-shrink-0" />
            )}

            <Layers className="w-3.5 h-3.5 text-primary flex-shrink-0" />
            <span className="font-semibold truncate text-[hsl(var(--foreground))]" title={spanName}>
              {spanName}
            </span>
            <span className="font-mono text-[10px] text-[hsl(var(--muted-foreground))]">
              ({serviceName})
            </span>
          </div>

          {/* Span ID */}
          <div className="col-span-2 font-mono text-[10px] text-[hsl(var(--muted-foreground))] truncate" title={spanId}>
            {spanId}
          </div>

          {/* Duration */}
          <div className="col-span-1 font-mono font-medium text-xs">
            {durationMs} ms
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
              title={`${spanName}: ${durationMs} ms (${leftPct.toFixed(1)}% start offset)`}
            />
          </div>
        </div>

        {/* Recursive child span rendering */}
        {!isCollapsed && hasChildren && childrenList.map((child) => renderSpanRow(child, depth + 1))}
      </React.Fragment>
    );
  };

  return (
    <div className="traces-container">
      {/* Back Button & Top Action */}
      <div className="flex items-center justify-between">
        <Link href="/traces" className="text-xs text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] flex items-center gap-1.5 transition-colors">
          <ArrowLeft size={14} />
          <span>{TRACES_TEXT.WATERFALL_BACK_LINK}</span>
        </Link>
        <span className="font-mono text-xs text-[hsl(var(--muted-foreground))]">{TRACES_TEXT.WATERFALL_TRACE_ID_LABEL} <strong className="text-primary">{trace.trace_id || '-'}</strong></span>
      </div>

      {/* Main Flame Graph Container */}
      <div className="traces-card-panel">
        {/* Header Summary */}
        <div className="waterfall-header-bar">
          <div>
            <h2 className="text-lg font-bold text-[hsl(var(--foreground))] flex items-center gap-2">
              <span>{trace.root_span_name || 'Root Operation'}</span>
            </h2>
            <div className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-4 mt-1">
              <span className="flex items-center gap-1.5"><Clock size={13} className="text-blue-500" /> {TRACES_TEXT.WATERFALL_TOTAL_DURATION} <strong className="text-[hsl(var(--foreground))] font-mono">{totalDuration} ms</strong></span>
              <span className="flex items-center gap-1.5"><Cpu size={13} className="text-indigo-500" /> {TRACES_TEXT.WATERFALL_TOTAL_SPANS} <strong className="text-[hsl(var(--foreground))] font-mono">{spansList.length}</strong></span>
            </div>
          </div>

          <div className="text-xs text-[hsl(var(--muted-foreground))] flex items-center gap-1.5 bg-[hsl(var(--muted)/0.3)] px-3 py-1.5 rounded-lg border border-[hsl(var(--border))]">
            <Info size={13} className="text-primary" />
            <span>{TRACES_TEXT.WATERFALL_CLICK_INFO}</span>
          </div>
        </div>

        {/* Flame Graph Waterfall Grid */}
        <div className="waterfall-tree-card">
          {/* Header Row with Timeline Scale Ticks */}
          <div className="grid grid-cols-12 py-2 px-3 bg-[hsl(var(--muted)/0.4)] border-b border-[hsl(var(--border))] text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">
            <div className="col-span-4">{TRACES_TEXT.WATERFALL_COL_SPAN}</div>
            <div className="col-span-2">{TRACES_TEXT.WATERFALL_COL_ID}</div>
            <div className="col-span-1">{TRACES_TEXT.WATERFALL_COL_DURATION}</div>
            <div className="col-span-5 relative flex items-center justify-between px-1 font-mono text-[9px] font-semibold text-[hsl(var(--muted-foreground))]">
              {ticks.map((t, idx) => (
                <span key={idx}>{t} ms</span>
              ))}
            </div>
          </div>

          {/* Span Rows */}
          {spansList.map((s) => renderSpanRow(s, 0))}
        </div>
      </div>

      {/* Slide-over Span Attribute Inspection Drawer */}
      <SpanAttributeDrawer
        span={selectedSpan}
        totalTraceDurationMs={totalDuration}
        onClose={() => setSelectedSpan(null)}
      />
    </div>
  );
}
