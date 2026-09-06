import { type Rule, resolveRules } from "@observability/shared-infra";

export const COST_RULES: Rule[] = [
  {
    id: "RULE_COST_BUDGET_EXCEEDED",
    name: "Monthly USD Spend Exceeds Soft Budget Limit",
    category: "budget",
    priority: 90,
    effect: "deny",
    conditions: [{ field: "total_cost_usd", op: "greater_than", value: 1000 }],
  },
];

export async function evaluateCostRules(ctx: Record<string, unknown>): Promise<Rule[]> {
  return resolveRules(COST_RULES, ctx);
}
