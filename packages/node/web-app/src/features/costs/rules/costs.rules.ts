export interface CostRule {
  id: string;
  name: string;
  category: "budget" | "token_spike";
  priority: number;
  effect: "critical" | "warning" | "ok";
  conditions: Array<{
    field: string;
    op: "gt" | "gte" | "lt" | "lte" | "eq";
    value: number;
  }>;
}

export const COST_RULES: CostRule[] = [
  {
    id: "RULE_COST_BUDGET_EXCEEDED",
    name: "Monthly USD Spend Exceeds Soft Budget Limit",
    category: "budget",
    priority: 90,
    effect: "warning",
    conditions: [{ field: "total_cost_usd", op: "gt", value: 1000 }],
  },
];
