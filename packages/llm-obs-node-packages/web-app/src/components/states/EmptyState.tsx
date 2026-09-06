'use client';

import React from 'react';
import { Inbox } from 'lucide-react';
import { cn } from '../../lib/utils/cn';

interface EmptyStateProps {
  /** Main heading */
  readonly title?: string;
  /** Descriptive explanation — not just "No data" */
  readonly description: string;
  /** Optional action element (e.g. a Button to create a resource) */
  readonly action?: React.ReactNode;
  /** Additional class names */
  readonly className?: string;
}

/**
 * F-08: EmptyState.
 * Clear explanation of why there is no data, never just "No data".
 * Composable into any data component.
 */
export function EmptyState({
  title = 'No data available',
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex min-h-[200px] w-full flex-col items-center justify-center rounded-lg border border-dashed border-[hsl(var(--border))] p-8 text-center',
        className
      )}
      role="status"
    >
      <div className="mb-3 rounded-full bg-[hsl(var(--muted))] p-3 text-[hsl(var(--muted-foreground))]">
        <Inbox size={24} aria-hidden="true" />
      </div>
      <h3 className="text-sm font-semibold text-[hsl(var(--foreground))]">{title}</h3>
      <p className="mt-1 max-w-sm text-xs text-[hsl(var(--muted-foreground))]">{description}</p>
      {action !== undefined && <div className="mt-4">{action}</div>}
    </div>
  );
}
