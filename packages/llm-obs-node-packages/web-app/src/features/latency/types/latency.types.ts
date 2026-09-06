export interface PercentilesResult {
  p50: number;
  p95: number;
  p99: number;
  sample_count: number;
}

export interface SLOResult {
  burn_fast: number;
  burn_medium: number;
  burn_slow: number;
  budget_remaining_pct: number;
  slo_threshold_ms: number;
}

export interface BaselinePoint {
  date: string;
  p99_ttft_ms: number;
  p99_total_ms: number;
}

export interface AttributionResult {
  dns: number;
  tcp: number;
  queue: number;
  inference: number;
}
