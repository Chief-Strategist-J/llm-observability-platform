import { z } from 'zod';

export const CostBreakdownItemSchema = z.object({
  model: z.string(),
  total_cost_usd_micro: z.number(),
  span_count: z.number(),
  avg_cost_usd_micro: z.number(),
});

export type CostBreakdownItem = z.infer<typeof CostBreakdownItemSchema>;

export const CostTimeSeriesPointSchema = z.object({
  timestamp: z.number(),
  cost_usd_micro: z.number(),
});

export type CostTimeSeriesPoint = z.infer<typeof CostTimeSeriesPointSchema>;

export const CostSummarySchema = z.object({
  total_cost_usd_micro: z.number(),
  daily_avg_cost_usd_micro: z.number(),
  cost_change_pct: z.number(),
  breakdown: z.array(CostBreakdownItemSchema),
  time_series: z.array(CostTimeSeriesPointSchema),
});

export type CostSummary = z.infer<typeof CostSummarySchema>;
