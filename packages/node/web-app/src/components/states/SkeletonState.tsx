'use client';

import React from 'react';
import { cn } from '../../lib/utils/cn';

interface SkeletonStateProps {
  /** Number of skeleton lines to render */
  readonly lines?: number;
  /** Additional class names */
  readonly className?: string;
}

/**
 * F-08: SkeletonState.
 * Composable loading placeholder. Every data component composes this
 * instead of rendering a bare spinner.
 */
export function SkeletonState({ lines = 3, className }: SkeletonStateProps) {
  if (lines < 1) {
    return null;
  }

  return (
    <div
      className={cn('w-full space-y-3 animate-pulse', className)}
      role="status"
      aria-label="Loading"
    >
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={cn(
            'h-4 rounded bg-[hsl(var(--muted))]',
            index === lines - 1 ? 'w-3/4' : 'w-full'
          )}
        />
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  );
}
