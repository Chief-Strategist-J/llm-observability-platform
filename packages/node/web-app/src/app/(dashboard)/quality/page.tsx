import React from 'react';
import { EmptyState } from '../../../components/states/EmptyState';

export default function QualityDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Quality & Evaluation</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Evaluate LLM output quality scores, hallucination flags, and feedback scores.
        </p>
      </div>

      <EmptyState
        title="Quality Intelligence Ready"
        description="Quality evaluation scores will be calculated as spans undergo automated evaluation."
      />
    </div>
  );
}
