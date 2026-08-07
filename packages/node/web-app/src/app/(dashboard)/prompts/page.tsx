import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function PromptsDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Prompt Intelligence</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Analyze prompt template effectiveness, token consumption, and version drift.
        </p>
      </div>

      <EmptyState
        title="Prompt Intelligence Ready"
        description="Prompt version metrics and usage telemetry will render here."
      />
    </div>
  );
}
