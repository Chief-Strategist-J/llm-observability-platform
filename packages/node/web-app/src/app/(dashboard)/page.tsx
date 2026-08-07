import React from 'react';
import { EmptyState } from '../../components/states/EmptyState';

export const dynamic = 'force-dynamic';

export default function OverviewDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Organization Overview</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Real-time summary of LLM latency, cost spend, and quality metrics across all services.
        </p>
      </div>

      <EmptyState
        title="Dashboard Overview Engine Ready"
        description="Connect your spans or select a service filter above to display live observability telemetry."
      />
    </div>
  );
}
