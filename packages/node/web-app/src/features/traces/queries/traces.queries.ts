export const TRACE_QUERIES = {
  QUERY_LIST_TRACES: {
    name: "listTraces",
    endpoint: "/api/v1/traces/list",
    description: "Fetch paginated distributed traces",
  },
  QUERY_TRACE_DETAIL: {
    name: "getTraceDetail",
    endpoint: "/api/v1/traces",
    description: "Fetch single trace span execution tree and waterfall DAG",
  },
} as const;
