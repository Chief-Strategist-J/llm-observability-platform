import { z } from 'zod';

export const PromptTemplateSchema = z.object({
  id: z.string(),
  name: z.string(),
  version: z.number(),
  content: z.string(),
  model: z.string(),
  usage_count: z.number(),
  avg_quality_score: z.number().optional(),
  avg_latency_ms: z.number().optional(),
  created_at: z.string(),
  updated_at: z.string(),
});

export type PromptTemplate = z.infer<typeof PromptTemplateSchema>;

export const PromptUsageStatSchema = z.object({
  template_id: z.string(),
  template_name: z.string(),
  invocation_count: z.number(),
  avg_latency_ms: z.number(),
  avg_cost_usd_micro: z.number(),
  avg_quality_score: z.number(),
});

export type PromptUsageStat = z.infer<typeof PromptUsageStatSchema>;

export const PromptAnalysisSchema = z.object({
  templates: z.array(PromptTemplateSchema),
  usage_stats: z.array(PromptUsageStatSchema),
  total_invocations: z.number(),
});

export type PromptAnalysis = z.infer<typeof PromptAnalysisSchema>;
