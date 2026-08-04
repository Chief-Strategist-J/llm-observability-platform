'use client';

import React, { useEffect, useRef } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
import { cn } from '../../../lib/cn';
import { formatLatencyMs } from '../../../lib/formatters';

interface PercentileBandChartProps {
  /** [timestamps[], p50[], p95[], p99[]] — DDSketch-shaped data */
  readonly data: [number[], number[], number[], number[]];
  readonly width?: number;
  readonly height?: number;
  readonly title?: string;
  readonly className?: string;
  /** Minimum sample count per bucket to consider bands reliable. */
  readonly minSampleSize?: number;
  /** Sample sizes per bucket — when provided, flags low-sample-size buckets (EC-FE1-02). */
  readonly sampleSizes?: readonly number[];
  /** When true, freezes animations for deterministic visual regression (RISK-FE1-03). */
  readonly testMode?: boolean;
}

/**
 * F-05: PercentileBand chart primitive (P50/P95/P99 ribbon).
 * - Takes DDSketch-shaped data directly — no client-side percentile math.
 * - Handles P50 > P95 on low-sample-size buckets without clipping or reordering (EC-FE1-02).
 * - testMode freezes animation for Chromatic snapshots.
 */
export function PercentileBandChart({
  data,
  width = 600,
  height = 250,
  title = 'Latency Percentile Bands',
  className,
  minSampleSize = 10,
  sampleSizes,
  testMode = false,
}: PercentileBandChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<uPlot | null>(null);

  // EC-FE1-02: Detect inverted bands caused by low sample sizes
  const hasInvertedBands = data[0].length > 0 && data[1].some((p50, i) => {
    const p95 = data[2][i];
    return p95 !== undefined && p50 > p95;
  });

  const hasLowSamples = sampleSizes !== undefined && sampleSizes.some((s) => s < minSampleSize);

  useEffect(() => {
    if (typeof window === 'undefined' || containerRef.current === null) return;

    const opts: uPlot.Options = {
      title,
      width,
      height,
      scales: { x: { time: true }, y: { auto: true } },
      series: [
        {}, // x axis
        {
          label: 'P50 (Median)',
          stroke: 'hsl(var(--primary))',
          width: 2,
          points: { show: false },
        },
        {
          label: 'P95',
          stroke: 'hsl(338 60% 60%)',
          width: 1.5,
          points: { show: false },
        },
        {
          label: 'P99 (Max)',
          stroke: 'hsl(var(--severity-bad))',
          width: 1.5,
          points: { show: false },
        },
      ],
      bands: [
        { series: [2, 1], fill: 'hsla(var(--primary), 0.15)' },
        { series: [3, 2], fill: 'hsla(338, 60%, 60%, 0.1)' },
      ],
      axes: [
        { grid: { show: true, stroke: 'rgba(255,255,255,0.05)' }, ticks: { show: true, stroke: 'rgba(255,255,255,0.1)' } },
        {
          grid: { show: true, stroke: 'rgba(255,255,255,0.05)' },
          ticks: { show: true, stroke: 'rgba(255,255,255,0.1)' },
          values: (_self: uPlot, splits: number[]) => splits.map((v) => formatLatencyMs(v)),
        },
      ],
      cursor: { drag: { setScale: false } },
    };

    const plot = new uPlot(opts, data, containerRef.current);
    plotRef.current = plot;

    return () => {
      plot.destroy();
      plotRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, width, height, title, testMode]);

  return (
    <div className={cn(className)}>
      <div
        ref={containerRef}
        className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4"
      />
      {/* EC-FE1-02: Visual flag for noisy/inverted bands */}
      {(hasInvertedBands || hasLowSamples) && (
        <p className="mt-2 text-xs text-[hsl(var(--severity-warn))]" role="status">
          ⚠ Some buckets have low sample sizes — percentile bands may appear inverted or noisy.
        </p>
      )}
    </div>
  );
}
