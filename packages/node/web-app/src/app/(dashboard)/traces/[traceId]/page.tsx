import React from 'react';
import { EmptyState } from '../../../../components/states/EmptyState';

interface TraceViewerPageProps {
  readonly params: Promise<{ traceId: string }>;
}

export default async function TraceViewerPage({ params }: TraceViewerPageProps) {
  const { traceId } = await params;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Trace: {traceId}</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          Inspect execution DAG, child spans, LLM prompts, and latency breakdown.
        </p>
      </div>

      <EmptyState
        title={`Trace ${traceId}`}
        description="Detailed span tree and execution waterfall will load here."
      />
    </div>
  );
}
