'use client';

import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '../../lib/cn';

interface ErrorStateProps {
  /** Error heading */
  readonly title?: string;
  /** Human-readable error message */
  readonly message: string;
  /** Retry callback — when provided, a retry button is rendered */
  readonly onRetry?: () => void;
  /** Additional class names */
  readonly className?: string;
}

/**
 * F-08: ErrorState.
 * Composable error placeholder with retry affordance where applicable.
 */
export function ErrorState({
  title = 'Failed to load data',
  message,
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex min-h-[200px] w-full flex-col items-center justify-center rounded-lg border border-[hsl(var(--severity-bad)/.2)] bg-[hsl(var(--severity-bad)/.05)] p-8 text-center',
        className
      )}
      role="alert"
    >
      <div className="mb-3 rounded-full bg-[hsl(var(--severity-bad)/.1)] p-3 text-[hsl(var(--severity-bad))]">
        <AlertCircle size={24} aria-hidden="true" />
      </div>
      <h3 className="text-sm font-semibold text-[hsl(var(--severity-bad))]">{title}</h3>
      <p className="mt-1 max-w-sm text-xs text-[hsl(var(--muted-foreground))]">{message}</p>
      {onRetry !== undefined && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center gap-1.5 rounded bg-[hsl(var(--severity-bad))] px-3 py-1.5 text-xs font-medium text-white transition-colors hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
        >
          <RefreshCw size={12} aria-hidden="true" />
          Retry
        </button>
      )}
    </div>
  );
}
