'use client';

import React, { Suspense } from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { EmptyState } from '../../../components/states/EmptyState';

function PromptsDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();

  return (
    <>
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <EmptyState
        title="Prompt Intelligence Ready"
        description={`Showing prompt metrics for ${filters.timeRange} range | Model: ${filters.model} | Service: ${filters.service} | Environment: ${filters.environment}`}
      />
    </>
  );
}

export default function PromptsDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Prompt Intelligence</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Analyze prompt template effectiveness, token consumption, and version drift.
        </p>
      </div>

      <Suspense fallback={<div className="h-10 animate-pulse bg-muted rounded" />}>
        <PromptsDashboardContent />
      </Suspense>
    </div>
  );
}
