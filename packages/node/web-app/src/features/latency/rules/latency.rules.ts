import { type Rule, resolveRules } from "@observability/shared-infra";

export const LATENCY_RULES: Rule[] = [
  {
    id: "RULE_SLO_BURN_CRITICAL",
    name: "Fast Burn Rate Exceeds Critical Threshold",
    category: "burn_rate",
    priority: 100,
    effect: "deny",
    conditions: [
      { field: "burn_fast", op: "greater_than", value: 14.4 },
    ],
  },
  {
    id: "RULE_SLO_BURN_WARNING",
    name: "Medium Burn Rate Exceeds Warning Threshold",
    category: "burn_rate",
    priority: 50,
    effect: "deny",
    conditions: [
      { field: "burn_medium", op: "greater_than", value: 6.0 },
    ],
  },
  {
    id: "RULE_LATENCY_P99_HIGH",
    name: "P99 Latency Spike Above 5000ms",
    category: "anomaly",
    priority: 80,
    effect: "deny",
    conditions: [
      { field: "p99", op: "greater_than", value: 5000 },
    ],
  },
];

export async function evaluateLatencyRules(ctx: Record<string, unknown>): Promise<Rule[]> {
  return resolveRules(LATENCY_RULES, ctx);
}
