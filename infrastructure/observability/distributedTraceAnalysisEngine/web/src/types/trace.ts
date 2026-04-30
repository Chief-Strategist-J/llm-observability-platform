export type Span = {
  span_id: { 0: string } | string;
  parent_span_id?: { 0: string } | string | null;
  service_name: string;
  operation_name: string;
  start_time_ns: number;
  duration_ns: number;
};

export type CriticalPathNode = {
  span_id: { 0: string } | string;
  contribution: number;
};

export type AnalysisResult = {
  trace_id: { 0: string } | string;
  cluster_id: number;
  anomaly: boolean;
  anomaly_scores?: Array<{ signal_name: string; score: number; threshold: number }>;
  total_duration_ns?: number;
  span_count?: number;
  critical_path?: { nodes: CriticalPathNode[] };
};
