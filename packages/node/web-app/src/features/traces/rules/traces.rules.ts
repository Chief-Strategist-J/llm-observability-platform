export interface TraceRule {
  id: string;
  name: string;
  category: "latency" | "error" | "token_usage";
  priority: number;
  effect: "critical" | "warning" | "ok";
  conditions: Array<{
    field: string;
    op: "gt" | "gte" | "lt" | "lte" | "eq";
    value: number | string;
  }>;
}

export const TRACE_RULES: TraceRule[] = [
  {
    id: "RULE_TRACE_ERROR_STATUS",
    name: "Span Execution Error Detected",
    category: "error",
    priority: 100,
    effect: "critical",
    conditions: [{ field: "status", op: "eq", value: "error" }],
  },
  {
    id: "RULE_TRACE_HIGH_DURATION",
    name: "Trace Duration Exceeds 3000ms",
    category: "latency",
    priority: 80,
    effect: "warning",
    conditions: [{ field: "duration_ms", op: "gt", value: 3000 }],
  },
];
