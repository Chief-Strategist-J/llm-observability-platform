export interface LatencyRule {
  id: string;
  name: string;
  category: "sla" | "burn_rate" | "anomaly";
  priority: number;
  effect: "warning" | "critical" | "ok";
  conditions: Array<{
    field: string;
    op: "gt" | "gte" | "lt" | "lte" | "eq";
    value: number;
  }>;
}

export const LATENCY_RULES: LatencyRule[] = [
  {
    id: "RULE_SLO_BURN_CRITICAL",
    name: "Fast Burn Rate Exceeds Critical Threshold",
    category: "burn_rate",
    priority: 100,
    effect: "critical",
    conditions: [
      { field: "burn_fast", op: "gt", value: 14.4 },
    ],
  },
  {
    id: "RULE_SLO_BURN_WARNING",
    name: "Medium Burn Rate Exceeds Warning Threshold",
    category: "burn_rate",
    priority: 50,
    effect: "warning",
    conditions: [
      { field: "burn_medium", op: "gt", value: 6.0 },
    ],
  },
  {
    id: "RULE_LATENCY_P99_HIGH",
    name: "P99 Latency Spike Above 5000ms",
    category: "anomaly",
    priority: 80,
    effect: "warning",
    conditions: [
      { field: "p99", op: "gt", value: 5000 },
    ],
  },
];
