'use client';

import React from 'react';
import { ErrorState } from '../components/states/ErrorState';

export default function GlobalError({
  error,
  reset,
}: {
  readonly error: Error & { digest?: string };
  readonly reset: () => void;
}) {
  return (
    <div className="flex min-h-[400px] w-full items-center justify-center p-6">
      <ErrorState
        message={error.message || 'An unexpected error occurred.'}
        onRetry={reset}
      />
    </div>
  );
}
