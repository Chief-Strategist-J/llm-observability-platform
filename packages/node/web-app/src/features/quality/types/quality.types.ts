export interface QualitySummaryResult {
  avg_quality_score: number;       // e.g. 0.94 (scale 0-1)
  score_delta_pct: number;         // e.g. +3.2%
  below_slo_count: number;         // e.g. 14 prompts below 0.85 threshold
  total_evaluated_prompts: number; // e.g. 12500
}

export interface QualityTrendPoint {
  date: string;                     // e.g. "2026-08-31T20:00:00Z"
  avg_quality_score: number;        // e.g. 0.92
  toxicity_alerts: number;          // e.g. 2
  hallucination_alerts: number;     // e.g. 5
}

export interface ModelQualityBreakdown {
  model: string;                    // e.g. "gpt-4o", "claude-3-opus", "gpt-4o-mini"
  avg_score: number;                // e.g. 0.96
  min_score: number;                // e.g. 0.72
  max_score: number;                // e.g. 0.99
  evaluation_count: number;         // e.g. 4200
  pass_rate_pct: number;            // e.g. 98.4%
}

export interface FlaggedContentAlert {
  id: string;
  span_id: string;
  alert_type: "toxicity" | "hallucination" | "pii_leak" | "bias";
  severity: "critical" | "warning" | "info";
  confidence_score: number;         // e.g. 0.94
  prompt_snippet: string;
  timestamp: string;
}
