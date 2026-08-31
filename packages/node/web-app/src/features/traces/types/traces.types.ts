import type { Span } from "@observability/api-types";

export type { Span };

export interface TraceSummary {
  id: string;
  root_span_name: string;
  service: string;
  model: string;
  duration_ms: number;
  total_tokens: number;
  cost_usd: number;
  status: "success" | "error";
  timestamp: string;
}

export interface SpanNode {
  id: string;
  parent_id?: string;
  name: string;
  kind: "SERVER" | "CLIENT" | "INTERNAL";
  service: string;
  model?: string;
  start_time_offset_ms: number;
  duration_ms: number;
  status: "success" | "error";
  attributes?: Record<string, string | number | boolean>;
  children?: SpanNode[];
}

export interface TraceDetailResult {
  trace_id: string;
  root_span_name: string;
  total_duration_ms: number;
  spans: SpanNode[];
}
