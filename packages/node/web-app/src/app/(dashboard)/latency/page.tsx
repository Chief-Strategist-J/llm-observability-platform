'use client';

import React from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { EmptyState } from '../../../components/states/EmptyState';

export default function LatencyDashboardPage() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Latency Analytics</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Monitor P50, P95, P99 percentile latency ribbons and TTFT (time-to-first-token).
        </p>
      </div>

      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <EmptyState
        title="Latency Analytics Ready"
        description={`Showing telemetry for ${filters.timeRange} range | Model: ${filters.model} | Service: ${filters.service} | Environment: ${filters.environment}`}
      />
    </div>
  );
}
