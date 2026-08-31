'use client';

import React, { Suspense } from 'react';
import { useDashboardFilters } from '../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../components/forms/DashboardFilterBar';
import { useOverviewDashboardData } from '@/features/overview/hooks';
import { OverviewDashboardUI } from '@/features/overview/ui/OverviewDashboardUI';

function OverviewDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();
  const { kpi, health, recentTraces, loading, error } = useOverviewDashboardData(filters);

  return (
    <div className="flex flex-col gap-6">
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <OverviewDashboardUI
        kpi={kpi}
        health={health}
        recentTraces={recentTraces}
        loading={loading}
        error={error}
      />
    </div>
  );
}

export default function OverviewDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Organization Overview</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Real-time summary of LLM latency, quality metrics, cost spend, and active OpenTelemetry streams.
        </p>
      </div>

      <Suspense fallback={<div className="h-10 animate-pulse bg-muted rounded" />}>
        <OverviewDashboardContent />
      </Suspense>
    </div>
  );
}
