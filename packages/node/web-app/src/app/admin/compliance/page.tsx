import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function AdminCompliancePage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Compliance & Data Residency</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Configure HIPAA, EU_ONLY, and prompt/response text redaction policies.
        </p>
      </div>

      <EmptyState
        title="Compliance Controls"
        description="Enforce zero-log prompt policies and data residency controls per organization."
      />
    </div>
  );
}
