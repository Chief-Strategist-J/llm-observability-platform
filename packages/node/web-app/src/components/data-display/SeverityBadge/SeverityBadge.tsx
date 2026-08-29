'use client';

import React from 'react';
import { tokens } from '@observability/design-tokens';
import { cn } from '../../../lib/utils/cn';

export type SeverityMetricType = 'latency' | 'cost' | 'quality';
export type SeverityLevel = 'good' | 'warn' | 'bad';

/**
 * Derives severity from a metric value using token-defined thresholds.
 * Single source of truth (EC-FE1-05) — thresholds come from design-tokens,
 * never hardcoded per-component.
 */
export function deriveSeverity(type: SeverityMetricType, value: number): SeverityLevel {
  const { latency_ms, cost_usd_micro, quality_score } = tokens.severity;

  switch (type) {
    case 'latency': {
      if (value <= latency_ms.good) return 'good';
      if (value <= latency_ms.warn) return 'warn';
      return 'bad';
    }
    case 'cost': {
      if (value <= cost_usd_micro.good) return 'good';
      if (value <= cost_usd_micro.warn) return 'warn';
      return 'bad';
    }
    case 'quality': {
      if (value >= quality_score.good) return 'good';
      if (value >= quality_score.warn) return 'warn';
      return 'bad';
    }
    default: {
      return 'bad';
    }
  }
}

const SEVERITY_CLASSES: Record<SeverityLevel, string> = {
  good: 'border-[hsl(var(--severity-good)/.3)] bg-[hsl(var(--severity-good)/.1)] text-[hsl(var(--severity-good))]',
  warn: 'border-[hsl(var(--severity-warn)/.3)] bg-[hsl(var(--severity-warn)/.1)] text-[hsl(var(--severity-warn))]',
  bad: 'border-[hsl(var(--severity-bad)/.3)] bg-[hsl(var(--severity-bad)/.1)] text-[hsl(var(--severity-bad))]',
} as const;

interface SeverityBadgeProps {
  /** Metric type used to derive the severity threshold. */
  readonly type: SeverityMetricType;
  /** Raw metric value — compared against token thresholds. */
  readonly value: number;
  /** Custom display label — defaults to formatted value + unit. */
  readonly label?: string;
  /** Additional class names. */
  readonly className?: string;
}

/**
 * F-03: SeverityBadge.
 * Maps quality/cost/latency thresholds to color using design-tokens
 * as the single source of truth.
 */
export function SeverityBadge({ type, value, label, className }: SeverityBadgeProps) {
  const severity = deriveSeverity(type, value);

  const defaultLabels: Record<SeverityMetricType, string> = {
    latency: `${value} ms`,
    cost: `${value} µ$`,
    quality: `${(value * 100).toFixed(0)}%`,
  };

  const displayLabel = label ?? defaultLabels[type];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-[var(--radius-sm)] border px-2 py-0.5 text-xs font-semibold',
        SEVERITY_CLASSES[severity],
        className
      )}
    >
      {displayLabel}
    </span>
  );
}
