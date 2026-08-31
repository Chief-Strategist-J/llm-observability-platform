export interface QualityRule {
  id: string;
  name: string;
  category: "sla" | "toxicity" | "hallucination" | "score_degradation";
  priority: number;
  effect: "critical" | "warning" | "ok";
  conditions: Array<{
    field: string;
    op: "gt" | "gte" | "lt" | "lte" | "eq";
    value: number;
  }>;
}

export const QUALITY_RULES: QualityRule[] = [
  {
    id: "RULE_QUALITY_SCORE_CRITICAL",
    name: "Average Quality Score Dropped Below 0.80",
    category: "score_degradation",
    priority: 100,
    effect: "critical",
    conditions: [
      { field: "avg_quality_score", op: "lt", value: 0.80 },
    ],
  },
  {
    id: "RULE_QUALITY_SCORE_WARNING",
    name: "Quality Score Below Target 0.85 SLO",
    category: "sla",
    priority: 50,
    effect: "warning",
    conditions: [
      { field: "avg_quality_score", op: "lt", value: 0.85 },
    ],
  },
  {
    id: "RULE_TOXICITY_ALERT_SPIKE",
    name: "Toxicity Alerts Exceed Threshold",
    category: "toxicity",
    priority: 90,
    effect: "critical",
    conditions: [
      { field: "toxicity_alerts", op: "gte", value: 5 },
    ],
  },
  {
    id: "RULE_HALLUCINATION_ALERT_SPIKE",
    name: "Hallucination Alerts Exceed Threshold",
    category: "hallucination",
    priority: 80,
    effect: "warning",
    conditions: [
      { field: "hallucination_alerts", op: "gte", value: 8 },
    ],
  },
];
