import { router, protectedProcedure } from '../trpc';
import { FilterStateSchema, MetricSummarySchema } from '@observability/api-types';
import { z } from 'zod';

const PercentilePointSchema = z.object({
  timestamp: z.number(),
  p50: z.number(),
  p95: z.number(),
  p99: z.number(),
});

export const latencyRouter = router({
  getSummary: protectedProcedure
    .input(FilterStateSchema.optional())
    .output(MetricSummarySchema)
    .query(() => {
      return {
        latency_p50: 180,
        latency_p95: 450,
        latency_p99: 620,
        total_cost_usd_micro: 5870,
        avg_quality_score: 0.82,
        total_tokens: 11040,
        span_count: 5,
      };
    }),

  getPercentiles: protectedProcedure
    .input(FilterStateSchema.optional())
    .output(z.array(PercentilePointSchema))
    .query(() => {
      return Array.from({ length: 60 }, (_, i) => ({
        timestamp: Date.now() - (60 - i) * 60000,
        p50: 150 + Math.sin(i / 10) * 30,
        p95: 350 + Math.sin(i / 10) * 50,
        p99: 500 + Math.sin(i / 10) * 80,
      }));
    }),
});
