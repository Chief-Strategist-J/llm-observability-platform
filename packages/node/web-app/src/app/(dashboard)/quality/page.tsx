'use client';

import React from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { EmptyState } from '../../../components/states/EmptyState';

export default function QualityDashboardPage() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quality & Evaluation</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Evaluate LLM output quality scores, hallucination flags, and feedback scores.
        </p>
      </div>

      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <EmptyState
        title="Quality Intelligence Ready"
        description={`Showing quality evaluation scores for ${filters.timeRange} range | Model: ${filters.model} | Service: ${filters.service} | Environment: ${filters.environment}`}
      />
    </div>
  );
}
