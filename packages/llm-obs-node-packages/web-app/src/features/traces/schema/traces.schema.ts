import { z } from "zod";
import type { JsonMapOp } from "../../../core/data-driven/transform.types";

export const TraceListQuerySchema = z.object({
  model: z.string().optional(),
  status: z.enum(["success", "error"]).optional(),
  service: z.string().optional(),
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
});

export const TraceSummaryFromApiOps: JsonMapOp[] = [
  { op: "coerce", key: "duration_ms", to: "number" },
  { op: "coerce", key: "total_tokens", to: "number" },
  { op: "coerce", key: "cost_usd", to: "number" },
];
