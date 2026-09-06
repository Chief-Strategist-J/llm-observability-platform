import { router, protectedProcedure } from '../trpc';
import { FilterStateSchema, QualitySummarySchema } from '@observability/api-types';

export const qualityRouter = router({
  getSummary: protectedProcedure
    .input(FilterStateSchema.optional())
    .output(QualitySummarySchema)
    .query(() => {
      return {
        avg_quality_score: 0.82,
        quality_change_pct: 2.1,
        below_slo_count: 3,
        by_model: [
          { model: 'gpt-4o', avg_quality_score: 0.92, span_count: 42, min_quality_score: 0.78, max_quality_score: 0.98 },
          { model: 'claude-3-opus', avg_quality_score: 0.85, span_count: 15, min_quality_score: 0.45, max_quality_score: 0.95 },
          { model: 'gpt-4o-mini', avg_quality_score: 0.78, span_count: 88, min_quality_score: 0.60, max_quality_score: 0.90 },
        ],
        trend: Array.from({ length: 24 }, (_, i) => ({
          timestamp: Date.now() - (24 - i) * 3600000,
          avg_quality_score: 0.80 + Math.sin(i / 8) * 0.05,
        })),
      };
    }),
});
