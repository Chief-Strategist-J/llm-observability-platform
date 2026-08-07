import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function AdminTemplatesPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Prompt Template Registry</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Manage system prompt versions, template variables, and deployment tags.
        </p>
      </div>

      <EmptyState
        title="Prompt Registry"
        description="Version-controlled prompt templates will render here for admin editing."
      />
    </div>
  );
}
