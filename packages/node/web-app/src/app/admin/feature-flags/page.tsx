import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function AdminFeatureFlagsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Feature Flag Management</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Toggle UI features, percentage rollouts, and rule-based targeting.
        </p>
      </div>

      <EmptyState
        title="Feature Flag Admin"
        description="Feature flag bundles resolved via the Rules Engine are managed here."
      />
    </div>
  );
}
