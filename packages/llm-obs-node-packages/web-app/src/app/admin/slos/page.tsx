import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function AdminSLOsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">SLO Threshold Editor</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Define latency (P95/P99), cost, and quality thresholds that trigger alerts.
        </p>
      </div>

      <EmptyState
        title="SLO Configurator"
        description="Threshold sliders configured here drive MetricCard and SeverityBadge color bands."
      />
    </div>
  );
}
