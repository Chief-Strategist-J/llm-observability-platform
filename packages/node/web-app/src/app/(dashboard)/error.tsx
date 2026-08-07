'use client';

import React from 'react';
import { ErrorState } from '../../components/states/ErrorState';

export default function DashboardError({
  error,
  reset,
}: {
  readonly error: Error & { digest?: string };
  readonly reset: () => void;
}) {
  return (
    <div className="flex min-h-[300px] w-full items-center justify-center p-6">
      <ErrorState
        message={error.message || 'Dashboard failed to load telemetry data.'}
        onRetry={reset}
      />
    </div>
  );
}
