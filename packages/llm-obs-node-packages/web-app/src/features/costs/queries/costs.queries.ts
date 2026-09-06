export const COST_QUERIES = {
  QUERY_COST_SUMMARY: {
    name: "getCostSummary",
    endpoint: "/api/v1/costs/summary",
    description: "Fetch aggregated cost spend metrics",
  },
  QUERY_COST_PROVIDERS: {
    name: "getCostProviders",
    endpoint: "/api/v1/costs/providers",
    description: "Fetch spend breakdown by provider and model",
  },
} as const;
