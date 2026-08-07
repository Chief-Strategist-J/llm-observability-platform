import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function AdminBudgetsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Budget Configuration</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Configure organization USD spend limits and threshold alerts.
        </p>
      </div>

      <EmptyState
        title="Budget Manager"
        description="Set monthly spending limits per team, model, or application environment."
      />
    </div>
  );
}
