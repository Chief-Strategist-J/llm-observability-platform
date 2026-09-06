import { z } from 'zod';
import { router, adminProcedure } from '../trpc';
import { BudgetSchema, SLOThresholdSchema } from '@observability/api-types';

export const adminRouter = router({
  budgets: router({
    list: adminProcedure
      .output(z.array(BudgetSchema))
      .query(() => {
        return [
          { id: 'budget-001', name: 'Q3 LLM Spend', limit_usd_micro: 50_000_000, spent_usd_micro: 32_450_000, start_date: '2026-07-01', end_date: '2026-09-30' },
          { id: 'budget-002', name: 'Embedding Pipeline', limit_usd_micro: 10_000_000, spent_usd_micro: 9_800_000, start_date: '2026-08-01', end_date: '2026-08-31' },
        ];
      }),

    update: adminProcedure
      .input(BudgetSchema)
      .output(BudgetSchema)
      .mutation(({ input }) => input),
  }),

  slos: router({
    list: adminProcedure
      .output(z.array(SLOThresholdSchema))
      .query(() => {
        return [
          { metric_name: 'latency_ms', good_threshold: 200, warning_threshold: 500 },
          { metric_name: 'cost_usd_micro', good_threshold: 1000, warning_threshold: 5000 },
          { metric_name: 'quality_score', good_threshold: 0.85, warning_threshold: 0.70 },
        ];
      }),

    update: adminProcedure
      .input(SLOThresholdSchema)
      .output(SLOThresholdSchema)
      .mutation(({ input }) => input),
  }),

  featureFlags: router({
    list: adminProcedure
      .output(z.array(z.object({
        id: z.string(),
        name: z.string(),
        enabled: z.boolean(),
        rollout_pct: z.number(),
      })))
      .query(() => {
        return [
          { id: 'experimental-dashboard', name: 'Experimental Dashboard', enabled: true, rollout_pct: 100 },
          { id: 'hipaa-redaction', name: 'HIPAA Redaction', enabled: false, rollout_pct: 0 },
        ];
      }),
  }),
});
