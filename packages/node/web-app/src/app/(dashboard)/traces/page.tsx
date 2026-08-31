'use client';

import React, { Suspense } from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { useTracesDashboardData } from '@/features/traces/hooks';
import { TracesDashboardUI } from '@/features/traces/ui/TracesDashboardUI';

function TracesDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();
  const { traces, loading, error } = useTracesDashboardData(filters);

  return (
    <div className="flex flex-col gap-6">
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <TracesDashboardUI
        traces={traces}
        loading={loading}
        error={error}
      />
    </div>
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
