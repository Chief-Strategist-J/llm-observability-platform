import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function LatencyDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Latency Analytics</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Monitor P50, P95, P99 percentile latency ribbons and TTFT (time-to-first-token).
        </p>
      </div>

      <EmptyState
        title="Latency Analytics Ready"
        description="P50/P95/P99 percentile bands will stream live once active spans are received."
      />
    </div>
  );
}
