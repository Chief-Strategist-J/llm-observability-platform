export const LATENCY_QUERIES = {
  FLOW_QUERY_PERCENTILES: {
    endpoint: "/v1/latency/percentiles",
    method: "GET",
    params: ["model", "hour_of_day", "quantiles"],
  },
  FLOW_QUERY_SLO: {
    endpoint: "/v1/latency/slo",
    method: "GET",
    params: ["model", "endpoint"],
  },
  FLOW_QUERY_BASELINE: {
    endpoint: "/v1/latency/baseline",
    method: "GET",
    params: ["model", "hour_of_day", "days"],
  },
  FLOW_QUERY_ATTRIBUTION: {
    endpoint: "/v1/latency/attribution",
    method: "GET",
    params: ["model", "hour"],
  },
} as const;
