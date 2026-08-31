import { z } from "zod";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";

export const OverviewQuerySchema = z.object({
  time_range: z.string().optional().default("24h"),
  environment: z.string().optional().default("production"),
});

export const OverviewKPIFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "p95_latency_ms", to: "number" },
  { op: "coerce", key: "quality_avg_score", to: "number" },
  { op: "coerce", key: "total_spend_usd", to: "number" },
  { op: "coerce", key: "active_spans_count", to: "number" },
  { op: "coerce", key: "p95_latency_delta_pct", to: "number" },
  { op: "coerce", key: "quality_delta_pct", to: "number" },
  { op: "coerce", key: "spend_delta_pct", to: "number" },
];
