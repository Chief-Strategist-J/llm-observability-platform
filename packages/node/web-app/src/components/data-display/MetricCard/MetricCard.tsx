'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '../../../lib/cn';
import { SkeletonState } from '../../states/SkeletonState';
import { EmptyState } from '../../states/EmptyState';
import { ErrorState } from '../../states/ErrorState';
import { type SeverityLevel } from '../SeverityBadge/SeverityBadge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../primitives/Tooltip';

interface DeltaValue {
  readonly value: string;
  readonly direction: 'up' | 'down';
  /** If true, the delta is neutral (no color coding). */
  readonly neutral?: boolean;
}

interface MetricCardProps {
  /** Label displayed above the value. */
  readonly label: string;
  /** Primary display value. */
  readonly value: string | number;
  /** Full-precision value shown in tooltip (EC-FE1-01). */
  readonly fullPrecisionValue?: string;
  /** Change indicator. */
  readonly delta?: DeltaValue;
  /** Sparkline data points. */
  readonly sparklineData?: readonly number[];
  /** Severity level — drives border/background color. */
  readonly severity?: SeverityLevel;
  /** Additional class names. */
  readonly className?: string;
  /** Dense mode for use inside DataTable or small cards. */
  readonly dense?: boolean;
}

const SEVERITY_BG: Record<SeverityLevel, string> = {
  good: 'border-[hsl(var(--severity-good)/.2)] bg-[hsl(var(--severity-good)/.05)]',
  warn: 'border-[hsl(var(--severity-warn)/.2)] bg-[hsl(var(--severity-warn)/.05)]',
  bad: 'border-[hsl(var(--severity-bad)/.2)] bg-[hsl(var(--severity-bad)/.05)]',
} as const;

const SEVERITY_DOT: Record<SeverityLevel, string> = {
  good: 'bg-[hsl(var(--severity-good))]',
  warn: 'bg-[hsl(var(--severity-warn))]',
  bad: 'bg-[hsl(var(--severity-bad))]',
} as const;

const SEVERITY_STROKE: Record<SeverityLevel, string> = {
  good: 'hsl(var(--severity-good))',
  warn: 'hsl(var(--severity-warn))',
  bad: 'hsl(var(--severity-bad))',
} as const;

/** Renders an inline SVG sparkline from an array of data points. */
function Sparkline({ data, severity }: { readonly data: readonly number[]; readonly severity?: SeverityLevel }) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 120;
  const height = 40;

  const points = data
    .map((val, index) => {
      const x = (index / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * (height - 4) + 2;
      return `${x},${y}`;
    })
    .join(' ');

  const strokeColor = severity !== undefined ? SEVERITY_STROKE[severity] : 'hsl(var(--primary))';

  return (
    <svg width={width} height={height + 4} viewBox={`0 0 ${width} ${height + 4}`} className="overflow-visible">
      <polyline fill="none" stroke={strokeColor} strokeWidth="1.5" points={points} />
    </svg>
  );
}

/**
 * F-04: MetricCard.
 * The single most-reused component: label, value, delta, sparkline, severity.
 * Truncates long values with a tooltip showing full precision (EC-FE1-01).
 */
export function MetricCard({
  label,
  value,
  fullPrecisionValue,
  delta,
  sparklineData,
  severity,
  className,
  dense = false,
}: MetricCardProps) {
  const cardContent = (
    <div
      className={cn(
        'flex flex-col justify-between rounded-[var(--radius-xl)] border shadow-sm backdrop-blur-md transition-all hover:scale-[1.01]',
        severity !== undefined ? SEVERITY_BG[severity] : 'border-[hsl(var(--border))] bg-[hsl(var(--card))]',
        dense ? 'p-3' : 'p-6',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between">
        <span className={cn('font-medium text-[hsl(var(--muted-foreground))]', dense ? 'text-xs' : 'text-sm')}>
          {label}
        </span>
        {severity !== undefined && (
          <span className="inline-flex items-center rounded-full bg-[hsl(var(--muted))] px-1.5 py-0.5 text-xs font-medium text-[hsl(var(--muted-foreground))]">
            <span className={cn('mr-1.5 h-1.5 w-1.5 rounded-full', SEVERITY_DOT[severity])} />
            {severity.toUpperCase()}
          </span>
        )}
      </div>

      {/* Value + Sparkline */}
      <div className={cn('flex items-end justify-between', dense ? 'mt-2' : 'mt-4')}>
        <div className="flex flex-col">
          <span
            className={cn(
              'truncate font-bold tracking-tight text-[hsl(var(--foreground))]',
              dense ? 'max-w-[120px] text-xl' : 'max-w-[200px] text-3xl'
            )}
          >
            {value}
          </span>
          {delta !== undefined && (
            <span
              className={cn(
                'mt-1 inline-flex items-center gap-1 text-xs font-semibold',
                delta.neutral === true
                  ? 'text-[hsl(var(--muted-foreground))]'
                  : delta.direction === 'up'
                    ? 'text-[hsl(var(--severity-good))]'
                    : 'text-[hsl(var(--severity-bad))]'
              )}
            >
              {delta.direction === 'up' ? <ArrowUpRight size={12} aria-hidden="true" /> : <ArrowDownRight size={12} aria-hidden="true" />}
              {delta.value}
            </span>
          )}
        </div>
        {sparklineData !== undefined && sparklineData.length > 1 && (
          <div className="flex max-w-[120px] flex-grow items-center justify-end">
            <Sparkline data={sparklineData} severity={severity} />
          </div>
        )}
      </div>
    </div>
  );

  // EC-FE1-01: Long values get a tooltip with full precision
  if (fullPrecisionValue !== undefined) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>{cardContent}</TooltipTrigger>
          <TooltipContent>{fullPrecisionValue}</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return cardContent;
}

// -- Composed state variants for the "Done" component contract --

export function MetricCardLoading({ className, dense }: { readonly className?: string; readonly dense?: boolean }) {
  return (
    <div
      className={cn(
        'flex h-[140px] flex-col justify-between rounded-[var(--radius-xl)] border border-[hsl(var(--border))] bg-[hsl(var(--card))]',
        dense ? 'p-3' : 'p-6',
        className
      )}
    >
      <SkeletonState lines={3} />
    </div>
  );
}

export function MetricCardEmpty({ className }: { readonly className?: string }) {
  return (
    <EmptyState
      title="No metrics recorded"
      description="Metrics will appear here once your application starts generating telemetry data."
      className={className}
    />
  );
}

export function MetricCardError({
  message,
  onRetry,
  className,
}: {
  readonly message: string;
  readonly onRetry?: () => void;
  readonly className?: string;
}) {
  return <ErrorState message={message} onRetry={onRetry} className={className} />;
}
