import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function OrgSettingsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Organization Settings</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Manage workspace identity, API keys, webhook destinations, and billing.
        </p>
      </div>

      <EmptyState
        title="Organization Settings"
        description="API keys and webhook notification channels will be configured here."
      />
    </div>
  );
}
