export type Span = {
  span_id: string;
  parent_span_id?: string | null;
  service_name: string;
  operation_name: string;
  start_time_ns: number;
  duration_ns: number;
};

export type CriticalPathNode = {
  span_id: string;
  service: string;
  operation: string;
  self_time_ns: number;
  contribution: number;
};

export type AnalysisResult = {
  trace_id: string;
  cluster_id: number;
  fingerprint: {
    vector: number[];
  };
  anomaly_scores?: Array<{
    signal_name: string;
    score: number;
    is_anomalous?: boolean;
  }>;
  critical_path?: {
    nodes: CriticalPathNode[];
    total_duration_ns: number;
    critical_service?: string;
    optimization_opportunity?: boolean;
  };
  is_anomalous: boolean;
  confidence: number;
  // Additional properties from API response
  total_duration_ns?: number;
  span_count?: number;
};

export type AnomalyScore = {
  signal_name: string;
  score: number;
  is_anomalous?: boolean;
};

export type Trace = {
  trace_id: string;
  spans: Span[];
};
