export interface OverviewRule {
  id: string;
  name: string;
  category: "system_health" | "cost" | "performance";
  priority: number;
  effect: "critical" | "warning" | "ok";
  conditions: Array<{
    field: string;
    op: "gt" | "gte" | "lt" | "lte" | "eq";
    value: number;
  }>;
}

export const OVERVIEW_RULES: OverviewRule[] = [
  {
    id: "RULE_SYSTEM_CRITICAL_BURN",
    name: "System SLO Fast Burn Rate Active",
    category: "system_health",
    priority: 100,
    effect: "critical",
    conditions: [{ field: "fast_burn_active", op: "eq", value: 1 }],
  },
  {
    id: "RULE_SYSTEM_P95_SPIKE",
    name: "P95 System Latency Above 1000ms",
    category: "performance",
    priority: 80,
    effect: "warning",
    conditions: [{ field: "p95_latency_ms", op: "gt", value: 1000 }],
  },
];
