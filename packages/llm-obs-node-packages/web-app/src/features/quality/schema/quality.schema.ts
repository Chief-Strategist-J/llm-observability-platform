import { z } from "zod";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";
import { QUALITY_CONFIG_DEFAULTS } from "../constants";

export const QualitySummaryQuerySchema = z.object({
  model: z.string().optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL),
  time_range: z.string().optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE),
  service: z.string().optional(),
});

export const QualityTrendQuerySchema = z.object({
  model: z.string().optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_MODEL),
  days: z.coerce.number().int().min(1).max(90).optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_LOOKBACK_DAYS),
});

export const ModelQualityQuerySchema = z.object({
  time_range: z.string().optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_TIME_RANGE),
});

export const FlaggedContentQuerySchema = z.object({
  severity: z.enum(["critical", "warning", "info"]).optional(),
  limit: z.coerce.number().int().min(1).max(100).optional().default(QUALITY_CONFIG_DEFAULTS.DEFAULT_LIMIT),
});

export const QualitySummaryFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "avg_quality_score", to: "number" },
  { op: "coerce", key: "score_delta_pct", to: "number" },
  { op: "coerce", key: "below_slo_count", to: "number" },
  { op: "coerce", key: "total_evaluated_prompts", to: "number" },
  { op: "default", key: "below_slo_count", value: 0 },
];

export const ModelQualityFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "avg_score", to: "number" },
  { op: "coerce", key: "min_score", to: "number" },
  { op: "coerce", key: "max_score", to: "number" },
  { op: "coerce", key: "evaluation_count", to: "number" },
  { op: "coerce", key: "pass_rate_pct", to: "number" },
];
