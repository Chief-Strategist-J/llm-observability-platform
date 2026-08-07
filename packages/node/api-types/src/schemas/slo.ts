import { z } from 'zod';

export const SLOThresholdSchema = z.object({
  metric_name: z.enum(['latency_ms', 'cost_usd_micro', 'quality_score']),
  good_threshold: z.number(),
  warning_threshold: z.number(),
});

export type SLOThreshold = z.infer<typeof SLOThresholdSchema>;
