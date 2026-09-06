import { type Rule, resolveRules } from "@observability/shared-infra";

export const TRACE_RULES: Rule[] = [
  {
    id: "RULE_TRACE_ERROR_STATUS",
    name: "Span Execution Error Detected",
    category: "error",
    priority: 100,
    effect: "deny",
    conditions: [{ field: "status", op: "equals", value: "error" }],
  },
  {
    id: "RULE_TRACE_HIGH_DURATION",
    name: "Trace Duration Exceeds 3000ms",
    category: "latency",
    priority: 80,
    effect: "deny",
    conditions: [{ field: "duration_ms", op: "greater_than", value: 3000 }],
  },
];

export async function evaluateTraceRules(ctx: Record<string, unknown>): Promise<Rule[]> {
  return resolveRules(TRACE_RULES, ctx);
}
