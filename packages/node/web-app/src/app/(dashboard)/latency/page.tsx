'use client';

import React, { Suspense } from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { useLatencyDashboardData } from '@/features/latency/hooks';
import { LatencyDashboardUI } from '@/features/latency/ui/LatencyDashboardUI';

function LatencyDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();
  const { percentiles, slo, attribution, baseline, loading, error } = useLatencyDashboardData(filters);

  return (
    <div className="flex flex-col gap-6">
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <LatencyDashboardUI
        percentiles={percentiles}
        slo={slo}
        attribution={attribution}
        baseline={baseline}
        loading={loading}
        error={error}
      />
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
