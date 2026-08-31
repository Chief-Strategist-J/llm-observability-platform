export interface OverviewKPIAggregates {
  p95_latency_ms: number;         // e.g. 340
  quality_avg_score: number;      // e.g. 0.94
  total_spend_usd: number;        // e.g. 1420.50
  active_spans_count: number;     // e.g. 84200
  p95_latency_delta_pct: number;  // e.g. -4.2
  quality_delta_pct: number;      // e.g. +2.1
  spend_delta_pct: number;        // e.g. +5.8
}

export interface SystemHealthSLOBanner {
  status: "healthy" | "warning" | "critical";
  fast_burn_active: boolean;
  medium_burn_active: boolean;
  active_alerts_count: number;
  message: string;
}

export interface RecentTracePreview {
  id: string;
  span_name: string;
  service: string;
  model: string;
  duration_ms: number;
  cost_usd: number;
  status: "success" | "error";
  timestamp: string;
}
