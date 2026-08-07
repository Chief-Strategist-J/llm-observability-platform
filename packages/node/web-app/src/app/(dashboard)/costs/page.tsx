import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function CostDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Cost Analytics</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Track USD spend breakdown by provider, model, and service pipeline.
        </p>
      </div>

      <EmptyState
        title="Cost Analytics Ready"
        description="Cost telemetry streams will populate here once API requests are recorded."
      />
    </div>
  );
}
