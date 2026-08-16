import { router, protectedProcedure } from '../trpc';
import { FilterStateSchema, PromptAnalysisSchema } from '@observability/api-types';

export const promptRouter = router({
  getAnalysis: protectedProcedure
    .input(FilterStateSchema.optional())
    .output(PromptAnalysisSchema)
    .query(() => {
      return {
        total_invocations: 1450,
        templates: [
          {
            id: 'tmpl-001', name: 'Summarize Document', version: 3,
            content: 'Summarize the following document...', model: 'gpt-4o',
            usage_count: 820, avg_quality_score: 0.91, avg_latency_ms: 210,
            created_at: '2026-07-01T00:00:00Z', updated_at: '2026-08-01T00:00:00Z',
          },
          {
            id: 'tmpl-002', name: 'Extract Entities', version: 2,
            content: 'Extract all named entities...', model: 'gpt-4o-mini',
            usage_count: 630, avg_quality_score: 0.85, avg_latency_ms: 120,
            created_at: '2026-07-15T00:00:00Z', updated_at: '2026-08-10T00:00:00Z',
          },
        ],
        usage_stats: [
          { template_id: 'tmpl-001', template_name: 'Summarize Document', invocation_count: 820, avg_latency_ms: 210, avg_cost_usd_micro: 850, avg_quality_score: 0.91 },
          { template_id: 'tmpl-002', template_name: 'Extract Entities', invocation_count: 630, avg_latency_ms: 120, avg_cost_usd_micro: 200, avg_quality_score: 0.85 },
        ],
      };
    }),
});
