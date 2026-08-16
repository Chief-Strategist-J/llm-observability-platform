'use client';

import React, { useEffect } from 'react';
import { ErrorState } from '../components/states/ErrorState';
import { captureExceptionWithTrace } from '../lib/sentry';

export default function GlobalError({
  error,
  reset,
}: {
  readonly error: Error & { digest?: string };
  readonly reset: () => void;
}) {
  useEffect(() => {
    captureExceptionWithTrace(error, error.digest);
  }, [error]);

  return (
    <div className="flex min-h-[400px] w-full items-center justify-center p-6">
      <ErrorState
        message={error.message || 'An unexpected error occurred.'}
        onRetry={reset}
      />
    </div>
  );
}
