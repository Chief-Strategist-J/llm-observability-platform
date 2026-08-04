export interface Span {
  trace_id: string;
  span_id: string;
  parent_span_id?: string;
  name: string;
  start_time_ms: number;
  end_time_ms: number;
  latency_ms: number;
  status: 'success' | 'error';
  cost_usd_micro: number;
  model: string;
  quality_score?: number;
  tokens_input?: number;
  tokens_output?: number;
  error_message?: string;
}

export interface MetricSummary {
  latency_p50: number;
  latency_p95: number;
  latency_p99: number;
  total_cost_usd_micro: number;
  avg_quality_score: number;
  total_tokens: number;
  span_count: number;
}

export interface Budget {
  id: string;
  name: string;
  limit_usd_micro: number;
  spent_usd_micro: number;
  start_date: string;
  end_date: string;
}

export interface SLOThreshold {
  metric_name: 'latency_ms' | 'cost_usd_micro' | 'quality_score';
  good_threshold: number;
  warning_threshold: number;
}

export interface Alert {
  id: string;
  title: string;
  severity: 'good' | 'warn' | 'bad';
  active: boolean;
  triggered_at: string;
}
