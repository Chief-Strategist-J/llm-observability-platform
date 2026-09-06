import { z } from 'zod';
import { router, protectedProcedure } from '../trpc';
import { TraceListItemSchema } from '@observability/api-types';

export const traceRouter = router({
  list: protectedProcedure
    .input(z.object({
      limit: z.number().min(1).max(100).default(50),
      cursor: z.string().optional(),
    }).optional())
    .output(z.object({
      items: z.array(TraceListItemSchema),
      nextCursor: z.string().optional(),
    }))
    .query(({ input }) => {
      const limit = input?.limit ?? 50;
      return {
        items: Array.from({ length: Math.min(limit, 5) }, (_, i) => ({
          trace_id: `trace-${String(i + 1).padStart(3, '0')}`,
          name: ['llm.completion', 'llm.embedding', 'llm.rerank'][i % 3] ?? 'llm.completion',
          total_latency_ms: 100 + i * 80,
          total_cost_usd_micro: 500 + i * 200,
          span_count: 1 + i,
          status: i === 2 ? 'error' as const : 'success' as const,
          started_at: new Date(Date.now() - i * 60000).toISOString(),
          model: ['gpt-4o', 'text-embedding-3-small', 'cohere-rerank-v3'][i % 3] ?? 'gpt-4o',
        })),
        nextCursor: undefined,
      };
    }),
});
