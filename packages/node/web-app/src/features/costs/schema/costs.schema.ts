import { z } from "zod";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";

export const CostSummaryQuerySchema = z.object({
  time_range: z.string().optional().default("30d"),
  provider: z.string().optional(),
});

export const CostSummaryFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "total_cost_usd", to: "number" },
  { op: "coerce", key: "daily_avg_usd", to: "number" },
  { op: "coerce", key: "cost_delta_pct", to: "number" },
  { op: "coerce", key: "projected_monthly_usd", to: "number" },
];
