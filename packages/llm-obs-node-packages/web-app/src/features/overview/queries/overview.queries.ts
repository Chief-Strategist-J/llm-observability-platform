export const OVERVIEW_QUERIES = {
  QUERY_KPI_SUMMARY: {
    name: "getKPISummary",
    endpoint: "/api/v1/overview/summary",
    description: "Fetch aggregated system KPI metrics",
  },
  QUERY_SYSTEM_HEALTH: {
    name: "getSystemHealth",
    endpoint: "/api/v1/overview/health",
    description: "Fetch system SLO health status and active burn rate alerts",
  },
} as const;
