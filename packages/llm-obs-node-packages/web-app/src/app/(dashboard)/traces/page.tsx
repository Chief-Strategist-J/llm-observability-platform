'use client';

import React, { useEffect, Suspense } from 'react';
import { useAppDispatch, useAppSelector } from '@/core/store';
import { tracesActions } from '@/features/traces/traces.slice';
import { TracesDashboardUI } from '@/features/traces/ui/TracesDashboardUI';

function TracesDashboardContent() {
  const dispatch = useAppDispatch();
  const traces = useAppSelector((state) => state.traces?.traces || []);
  const filters = useAppSelector((state) => state.traces?.filters || {
    searchQuery: '',
    selectedService: 'all',
    selectedStatus: 'all',
    selectedModel: 'all',
    minDurationMs: 0,
  });
  const status = useAppSelector((state) => state.traces?.status || 'idle');
  const error = useAppSelector((state) => state.traces?.error || null);

  useEffect(() => {
    dispatch(tracesActions.fetchTracesSubmitted());
  }, [dispatch]);

  return (
    <TracesDashboardUI
      traces={traces}
      filters={filters}
      loading={status === 'loading'}
      error={error}
      onSearchChange={(q) => dispatch(tracesActions.setSearchQuery(q))}
      onServiceChange={(s) => dispatch(tracesActions.setSelectedService(s))}
      onStatusChange={(st) => dispatch(tracesActions.setSelectedStatus(st))}
      onModelChange={(m) => dispatch(tracesActions.setSelectedModel(m))}
      onMinDurationChange={(d) => dispatch(tracesActions.setMinDurationMs(d))}
      onResetFilters={() => dispatch(tracesActions.resetFilters())}
    />
  );
}

export default function TracesDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trace Explorer</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Search and inspect distributed execution spans, OpenTelemetry trace trees, and latency bottlenecks.
        </p>
      </div>

      <Suspense fallback={<div className="h-10 animate-pulse bg-muted rounded" />}>
        <TracesDashboardContent />
      </Suspense>
    </div>
  );
}
