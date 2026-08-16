import { router, protectedProcedure } from '../trpc';
import { FilterStateSchema, CostSummarySchema } from '@observability/api-types';

export const costRouter = router({
  getSummary: protectedProcedure
    .input(FilterStateSchema.optional())
    .output(CostSummarySchema)
    .query(() => {
      return {
        total_cost_usd_micro: 5870,
        daily_avg_cost_usd_micro: 1957,
        cost_change_pct: -3.2,
        breakdown: [
          { model: 'gpt-4o', total_cost_usd_micro: 3200, span_count: 42, avg_cost_usd_micro: 762 },
          { model: 'claude-3-opus', total_cost_usd_micro: 1800, span_count: 15, avg_cost_usd_micro: 1200 },
          { model: 'gpt-4o-mini', total_cost_usd_micro: 870, span_count: 88, avg_cost_usd_micro: 99 },
        ],
        time_series: Array.from({ length: 24 }, (_, i) => ({
          timestamp: Date.now() - (24 - i) * 3600000,
          cost_usd_micro: 200 + Math.floor(Math.random() * 100),
        })),
      };
    }),
});
