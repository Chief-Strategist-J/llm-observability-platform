import { z } from 'zod';
import { SpanSchema } from './span.js';

export type TraceSpanNode = {
  span: z.infer<typeof SpanSchema>;
  children: TraceSpanNode[];
};

export const TraceSpanNodeSchema: z.ZodType<TraceSpanNode> = z.object({
  span: SpanSchema,
  children: z.array(z.lazy(() => TraceSpanNodeSchema)),
});

export const TraceDetailSchema = z.object({
  trace_id: z.string(),
  root_span: TraceSpanNodeSchema,
  total_latency_ms: z.number(),
  total_cost_usd_micro: z.number(),
  span_count: z.number(),
  status: z.enum(['success', 'error', 'partial']),
  started_at: z.string(),
});

export type TraceDetail = z.infer<typeof TraceDetailSchema>;

export const TraceListItemSchema = z.object({
  trace_id: z.string(),
  name: z.string(),
  total_latency_ms: z.number(),
  total_cost_usd_micro: z.number(),
  span_count: z.number(),
  status: z.enum(['success', 'error', 'partial']),
  started_at: z.string(),
  model: z.string(),
});

export type TraceListItem = z.infer<typeof TraceListItemSchema>;
