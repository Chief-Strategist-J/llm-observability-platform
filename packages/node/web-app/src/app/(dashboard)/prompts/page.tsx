'use client';

import React from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { EmptyState } from '../../../components/states/EmptyState';

export default function PromptsDashboardPage() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Prompt Intelligence</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Analyze prompt template effectiveness, token consumption, and version drift.
        </p>
      </div>

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
    </div>
  );
}
