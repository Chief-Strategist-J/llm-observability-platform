import { type Rule, resolveRules } from "@observability/shared-infra";

export const QUALITY_RULES: Rule[] = [
  {
    id: "RULE_QUALITY_SCORE_CRITICAL",
    name: "Average Quality Score Dropped Below 0.80",
    category: "score_degradation",
    priority: 100,
    effect: "deny",
    conditions: [
      { field: "avg_quality_score", op: "less_than", value: 0.80 },
    ],
  },
  {
    id: "RULE_QUALITY_SCORE_WARNING",
    name: "Quality Score Below Target 0.85 SLO",
    category: "sla",
    priority: 50,
    effect: "deny",
    conditions: [
      { field: "avg_quality_score", op: "less_than", value: 0.85 },
    ],
  },
  {
    id: "RULE_TOXICITY_ALERT_SPIKE",
    name: "Toxicity Alerts Exceed Threshold",
    category: "toxicity",
    priority: 90,
    effect: "deny",
    conditions: [
      { field: "toxicity_alerts", op: "greater_than", value: 5 },
    ],
  },
];

export async function evaluateQualityRules(ctx: Record<string, unknown>): Promise<Rule[]> {
  return resolveRules(QUALITY_RULES, ctx);
}
