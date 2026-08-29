import { z } from "zod";
import type { JsonMapOp } from "@/core/data-driven/transform.types";

export const PercentilesQuerySchema = z.object({
  model: z.string().min(1),
  hour_of_day: z.coerce.number().int().min(0).max(23),
  quantiles: z.string().optional().default("0.50,0.95,0.99"),
});

export const SLOQuerySchema = z.object({
  model: z.string().min(1),
  endpoint: z.string().min(1),
});

export const BaselineQuerySchema = z.object({
  model: z.string().min(1),
  hour_of_day: z.coerce.number().int().min(0).max(23),
  days: z.coerce.number().int().min(1).max(90).optional().default(7),
});

export const AttributionQuerySchema = z.object({
  model: z.string().min(1),
  hour: z.string().min(10).max(10),
});

export const PercentilesFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "p50", to: "number" },
  { op: "coerce", key: "p95", to: "number" },
  { op: "coerce", key: "p99", to: "number" },
  { op: "coerce", key: "sample_count", to: "number" },
  { op: "default", key: "sample_count", value: 0 },
];

export const SLOFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "burn_fast", to: "number" },
  { op: "coerce", key: "burn_medium", to: "number" },
  { op: "coerce", key: "burn_slow", to: "number" },
  { op: "coerce", key: "budget_remaining_pct", to: "number" },
  { op: "coerce", key: "slo_threshold_ms", to: "number" },
];
