'use client';

import React from 'react';
import { ErrorState } from '../../components/states/ErrorState';

export default function AdminError({
  error,
  reset,
}: {
  readonly error: Error & { digest?: string };
  readonly reset: () => void;
}) {
  return (
    <div className="flex min-h-[300px] w-full items-center justify-center p-6">
      <ErrorState
        message={error.message || 'Admin configuration operation failed.'}
        onRetry={reset}
      />
    </div>
  );
}
