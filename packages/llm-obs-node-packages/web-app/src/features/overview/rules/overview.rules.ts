import { type Rule, resolveRules } from "@observability/shared-infra";

export const OVERVIEW_RULES: Rule[] = [
  {
    id: "RULE_SYSTEM_CRITICAL_BURN",
    name: "System SLO Fast Burn Rate Active",
    category: "system_health",
    priority: 100,
    effect: "deny",
    conditions: [{ field: "fast_burn_active", op: "equals", value: true }],
  },
  {
    id: "RULE_SYSTEM_P95_SPIKE",
    name: "P95 System Latency Above 1000ms",
    category: "performance",
    priority: 80,
    effect: "deny",
    conditions: [{ field: "p95_latency_ms", op: "greater_than", value: 1000 }],
  },
];

export async function evaluateOverviewRules(ctx: Record<string, unknown>): Promise<Rule[]> {
  return resolveRules(OVERVIEW_RULES, ctx);
}
