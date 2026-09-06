/**
 * Type-derived fixture data for Storybook stories (EC-FE1-06).
 * Generated from the same TypeScript types as the real API response
 * (packages/api-types), so a breaking API change can't hide behind
 * a stale hand-written fixture.
 */

import type { Span, MetricSummary, Budget, SLOThreshold, Alert } from '@observability/api-types';

// -- Spans --

export const FIXTURE_SPANS: readonly Span[] = [
  {
    trace_id: 'trace-001-abc',
    span_id: 'span-001',
    name: 'llm.completion',
    start_time_ms: 1722700000000,
    end_time_ms: 1722700000180,
    latency_ms: 180,
    status: 'success',
    cost_usd_micro: 850,
    model: 'gpt-4o',
    quality_score: 0.92,
    tokens_input: 1200,
    tokens_output: 340,
  },
  {
    trace_id: 'trace-002-def',
    span_id: 'span-002',
    parent_span_id: 'span-001',
    name: 'llm.embedding',
    start_time_ms: 1722700001000,
    end_time_ms: 1722700001045,
    latency_ms: 45,
    status: 'success',
    cost_usd_micro: 120,
    model: 'text-embedding-3-small',
    tokens_input: 500,
    tokens_output: 0,
  },
  {
    trace_id: 'trace-003-ghi',
    span_id: 'span-003',
    name: 'llm.completion',
    start_time_ms: 1722700002000,
    end_time_ms: 1722700002620,
    latency_ms: 620,
    status: 'error',
    cost_usd_micro: 3200,
    model: 'claude-3-opus',
    quality_score: 0.45,
    tokens_input: 4000,
    tokens_output: 1200,
    error_message: 'Context length exceeded: 128k token limit',
  },
  {
    trace_id: 'trace-004-jkl',
    span_id: 'span-004',
    name: 'llm.completion',
    start_time_ms: 1722700003000,
    end_time_ms: 1722700003350,
    latency_ms: 350,
    status: 'success',
    cost_usd_micro: 1500,
    model: 'gpt-4o-mini',
    quality_score: 0.78,
    tokens_input: 2200,
    tokens_output: 800,
  },
  {
    trace_id: 'trace-005-mno',
    span_id: 'span-005',
    name: 'llm.rerank',
    start_time_ms: 1722700004000,
    end_time_ms: 1722700004090,
    latency_ms: 90,
    status: 'success',
    cost_usd_micro: 200,
    model: 'cohere-rerank-v3',
    quality_score: 0.88,
    tokens_input: 800,
    tokens_output: 0,
  },
] as const satisfies readonly Span[];

// -- MetricSummary --

export const FIXTURE_METRIC_SUMMARY: MetricSummary = {
  latency_p50: 180,
  latency_p95: 450,
  latency_p99: 620,
  total_cost_usd_micro: 5870,
  avg_quality_score: 0.82,
  total_tokens: 11040,
  span_count: 5,
} as const satisfies MetricSummary;

// -- Budgets --

export const FIXTURE_BUDGETS: readonly Budget[] = [
  {
    id: 'budget-001',
    name: 'Q3 LLM Spend',
    limit_usd_micro: 50_000_000,
    spent_usd_micro: 32_450_000,
    start_date: '2026-07-01',
    end_date: '2026-09-30',
  },
  {
    id: 'budget-002',
    name: 'Embedding Pipeline',
    limit_usd_micro: 10_000_000,
    spent_usd_micro: 9_800_000,
    start_date: '2026-08-01',
    end_date: '2026-08-31',
  },
] as const satisfies readonly Budget[];

// -- SLO Thresholds --

export const FIXTURE_SLO_THRESHOLDS: readonly SLOThreshold[] = [
  { metric_name: 'latency_ms', good_threshold: 200, warning_threshold: 500 },
  { metric_name: 'cost_usd_micro', good_threshold: 1000, warning_threshold: 5000 },
  { metric_name: 'quality_score', good_threshold: 0.85, warning_threshold: 0.70 },
] as const satisfies readonly SLOThreshold[];

// -- Alerts --

export const FIXTURE_ALERTS: readonly Alert[] = [
  { id: 'alert-001', title: 'P99 latency exceeded 500ms', severity: 'bad', active: true, triggered_at: '2026-08-04T09:45:00Z' },
  { id: 'alert-002', title: 'Embedding budget 98% consumed', severity: 'warn', active: true, triggered_at: '2026-08-04T09:30:00Z' },
  { id: 'alert-003', title: 'Quality score recovered above SLO', severity: 'good', active: false, triggered_at: '2026-08-04T08:00:00Z' },
] as const satisfies readonly Alert[];

// -- Time series data for chart fixtures --

const NOW = Math.floor(Date.now() / 1000);
const HOUR = 3600;

function generateTimeSeries(count: number, baseFn: (i: number) => number): number[] {
  return Array.from({ length: count }, (_, i) => baseFn(i));
}

export const FIXTURE_TIMESERIES_TIMESTAMPS: number[] = generateTimeSeries(60, (i) => NOW - (60 - i) * (HOUR / 60));

export const FIXTURE_LATENCY_P50: number[] = generateTimeSeries(60, (i) => 150 + Math.sin(i / 10) * 30 + Math.random() * 10);
export const FIXTURE_LATENCY_P95: number[] = generateTimeSeries(60, (i) => 350 + Math.sin(i / 10) * 50 + Math.random() * 20);
export const FIXTURE_LATENCY_P99: number[] = generateTimeSeries(60, (i) => 500 + Math.sin(i / 10) * 80 + Math.random() * 30);

export const FIXTURE_SPARKLINE_LATENCY: readonly number[] = [150, 160, 180, 175, 190, 170, 165, 180, 200, 185, 170, 160];
export const FIXTURE_SPARKLINE_COST: readonly number[] = [800, 850, 900, 1100, 1050, 950, 980, 1200, 1150, 1000, 950, 900];
export const FIXTURE_SPARKLINE_QUALITY: readonly number[] = [0.85, 0.87, 0.82, 0.80, 0.83, 0.86, 0.88, 0.90, 0.87, 0.85, 0.84, 0.86];
