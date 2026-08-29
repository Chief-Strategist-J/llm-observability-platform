import { LATENCY_ENDPOINTS } from "../constants";

export const LATENCY_QUERIES = {
  FLOW_QUERY_PERCENTILES: {
    endpoint: LATENCY_ENDPOINTS.PERCENTILES,
    method: "GET",
    params: ["model", "hour_of_day", "quantiles"],
  },
  FLOW_QUERY_SLO: {
    endpoint: LATENCY_ENDPOINTS.SLO,
    method: "GET",
    params: ["model", "endpoint"],
  },
  FLOW_QUERY_BASELINE: {
    endpoint: LATENCY_ENDPOINTS.BASELINE,
    method: "GET",
    params: ["model", "hour_of_day", "days"],
  },
  FLOW_QUERY_ATTRIBUTION: {
    endpoint: LATENCY_ENDPOINTS.ATTRIBUTION,
    method: "GET",
    params: ["model", "hour"],
  },
} as const;
