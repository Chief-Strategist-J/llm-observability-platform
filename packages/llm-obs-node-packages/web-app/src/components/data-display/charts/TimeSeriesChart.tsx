'use client';

import React, { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react';
import uPlot from 'uplot';
import 'uplot/dist/uPlot.min.css';
import { cn } from '../../../lib/utils/cn';

export interface TimeSeriesChartRef {
  /** Append a data point without triggering a full remount (TEST-FE1-06). */
  readonly appendPoint: (timestamp: number, values: readonly number[]) => void;
  /** Replace all data. */
  readonly setData: (data: uPlot.AlignedData) => void;
}

interface SeriesConfig {
  readonly label: string;
  readonly stroke: string;
  readonly width?: number;
  readonly fill?: string;
}

interface TimeSeriesChartProps {
  readonly data: uPlot.AlignedData;
  readonly series: readonly SeriesConfig[];
  readonly width?: number;
  readonly height?: number;
  readonly title?: string;
  readonly className?: string;
  /** When true, freezes animations for deterministic visual regression (RISK-FE1-03). */
  readonly testMode?: boolean;
}

/**
 * F-06: TimeSeriesChart primitive (uPlot).
 * - Zero-remount live-append mode via imperative ref.
 * - Buffers incoming points when tab is backgrounded (EC-FE1-03).
 * - testMode prop freezes animation for Chromatic snapshots.
 */
export const TimeSeriesChart = forwardRef<TimeSeriesChartRef, TimeSeriesChartProps>(
  ({ data, series, width = 600, height = 250, title, className, testMode = false }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const plotRef = useRef<uPlot | null>(null);
    const bufferRef = useRef<Array<{ timestamp: number; values: readonly number[] }>>([]);

    // EC-FE1-03: Flush buffered points when tab regains visibility
    const flushBuffer = useCallback(() => {
      if (plotRef.current === null || bufferRef.current.length === 0) return;
      const currentData = plotRef.current.data;
      if (currentData === undefined) return;

      const newData = currentData.map((arr) => Array.from(arr as number[])) as uPlot.AlignedData;
      const xSeries = newData[0] as number[];

      for (const point of bufferRef.current) {
        xSeries.push(point.timestamp);
        for (let i = 0; i < point.values.length; i++) {
          const ySeries = newData[i + 1] as number[];
          if (point.values[i] !== undefined) {
            ySeries.push(point.values[i]!);
          }
        }
      }
      bufferRef.current = [];
      plotRef.current.setData(newData, false);
    }, []);

    useEffect(() => {
      const handleVisibilityChange = () => {
        if (document.visibilityState === 'visible') {
          flushBuffer();
        }
      };
      document.addEventListener('visibilitychange', handleVisibilityChange);
      return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
    }, [flushBuffer]);

    useImperativeHandle(ref, () => ({
      appendPoint: (timestamp: number, values: readonly number[]) => {
        // EC-FE1-03: Buffer when tab is hidden
        if (document.visibilityState === 'hidden') {
          bufferRef.current.push({ timestamp, values });
          return;
        }

        if (plotRef.current === null) return;
        const currentData = plotRef.current.data;
        if (currentData === undefined) return;

        const newData = currentData.map((arr) => Array.from(arr as number[])) as uPlot.AlignedData;
        const xSeries = newData[0] as number[];
        xSeries.push(timestamp);
        for (let i = 0; i < values.length; i++) {
          const ySeries = newData[i + 1] as number[];
          if (values[i] !== undefined) {
            ySeries.push(values[i]!);
          }
        }
        plotRef.current.setData(newData, false);
      },
      setData: (newData: uPlot.AlignedData) => {
        if (plotRef.current !== null) {
          plotRef.current.setData(newData);
        }
      },
    }));

    useEffect(() => {
      if (typeof window === 'undefined' || containerRef.current === null) return;

      const opts: uPlot.Options = {
        title: title,
        width: width,
        height: height,
        scales: { x: { time: true }, y: { auto: true } },
        series: [
          {}, // x axis
          ...series.map((s) => ({
            label: s.label,
            stroke: s.stroke,
            width: s.width ?? 2,
            fill: s.fill,
            points: { show: false },
          })),
        ],
        axes: [
          { grid: { show: true, stroke: 'rgba(255,255,255,0.05)' }, ticks: { show: true, stroke: 'rgba(255,255,255,0.1)' } },
          { grid: { show: true, stroke: 'rgba(255,255,255,0.05)' }, ticks: { show: true, stroke: 'rgba(255,255,255,0.1)' } },
        ],
        cursor: { drag: { setScale: false } },
      };

      const plot = new uPlot(opts, data, containerRef.current);
      plotRef.current = plot;

      return () => {
        plot.destroy();
        plotRef.current = null;
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps -- series identity is stable, we only rebuild on structural changes
    }, [series, width, height, title, testMode]);

    return (
      <div className={cn(className)}>
        <div
          ref={containerRef}
          className="rounded-[var(--radius-lg)] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4"
        />
      </div>
    );
  }
);
TimeSeriesChart.displayName = 'TimeSeriesChart';
