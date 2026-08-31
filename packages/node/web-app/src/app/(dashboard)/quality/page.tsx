'use client';

import React, { Suspense } from 'react';
import { useDashboardFilters } from '../../../hooks/useDashboardFilters';
import { DashboardFilterBar } from '../../../components/forms/DashboardFilterBar';
import { useQualityDashboardData } from '@/features/quality/hooks';
import { QualityDashboardUI } from '@/features/quality/ui/QualityDashboardUI';

function QualityDashboardContent() {
  const { filters, setFilter, resetFilters, hasActiveFilters } = useDashboardFilters();
  const { summary, trend, models, flaggedAlerts, loading, error } = useQualityDashboardData(filters);

  return (
    <div className="flex flex-col gap-6">
      <DashboardFilterBar
        filters={filters}
        onFilterChange={setFilter}
        onReset={resetFilters}
        hasActiveFilters={hasActiveFilters}
      />

      <QualityDashboardUI
        summary={summary}
        trend={trend}
        models={models}
        flaggedAlerts={flaggedAlerts}
        loading={loading}
        error={error}
      />
    </div>
  );
}

export default function QualityDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quality & Evaluation</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Evaluate LLM output quality scores, hallucination flags, toxicity alerts, and model performance.
        </p>
      </div>

      <Suspense fallback={<div className="h-10 animate-pulse bg-muted rounded" />}>
        <QualityDashboardContent />
      </Suspense>
    </div>
  );
}
