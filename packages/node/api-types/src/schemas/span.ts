import { z } from 'zod';

export const SpanSchema = z.object({
  trace_id: z.string(),
  span_id: z.string(),
  parent_span_id: z.string().optional(),
  name: z.string(),
  start_time_ms: z.number(),
  end_time_ms: z.number(),
  latency_ms: z.number(),
  status: z.enum(['success', 'error']),
  cost_usd_micro: z.number(),
  model: z.string(),
  quality_score: z.number().optional(),
  tokens_input: z.number().optional(),
  tokens_output: z.number().optional(),
  error_message: z.string().optional(),
});

export type Span = z.infer<typeof SpanSchema>;

export const MetricSummarySchema = z.object({
  latency_p50: z.number(),
  latency_p95: z.number(),
  latency_p99: z.number(),
  total_cost_usd_micro: z.number(),
  avg_quality_score: z.number(),
  total_tokens: z.number(),
  span_count: z.number(),
});

export type MetricSummary = z.infer<typeof MetricSummarySchema>;
