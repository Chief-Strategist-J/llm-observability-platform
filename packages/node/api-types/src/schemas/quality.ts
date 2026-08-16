import { z } from 'zod';

export const QualityByModelSchema = z.object({
  model: z.string(),
  avg_quality_score: z.number(),
  span_count: z.number(),
  min_quality_score: z.number(),
  max_quality_score: z.number(),
});

export type QualityByModel = z.infer<typeof QualityByModelSchema>;

export const QualityTrendPointSchema = z.object({
  timestamp: z.number(),
  avg_quality_score: z.number(),
});

export type QualityTrendPoint = z.infer<typeof QualityTrendPointSchema>;

export const QualitySummarySchema = z.object({
  avg_quality_score: z.number(),
  quality_change_pct: z.number(),
  below_slo_count: z.number(),
  by_model: z.array(QualityByModelSchema),
  trend: z.array(QualityTrendPointSchema),
});

export type QualitySummary = z.infer<typeof QualitySummarySchema>;
