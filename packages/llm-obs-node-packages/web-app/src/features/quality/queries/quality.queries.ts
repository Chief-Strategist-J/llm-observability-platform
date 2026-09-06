export const QUALITY_QUERIES = {
  QUERY_QUALITY_SUMMARY: {
    name: "getQualitySummary",
    endpoint: "/api/v1/quality/summary",
    description: "Fetch high-level aggregated evaluation quality metrics",
  },
  QUERY_QUALITY_TREND: {
    name: "getQualityTrend",
    endpoint: "/api/v1/quality/trend",
    description: "Fetch rolling time-series quality score trend data",
  },
  QUERY_MODEL_BREAKDOWN: {
    name: "getModelBreakdown",
    endpoint: "/api/v1/quality/models",
    description: "Fetch per-model evaluation score statistics",
  },
  QUERY_FLAGGED_CONTENT: {
    name: "getFlaggedContent",
    endpoint: "/api/v1/quality/flagged",
    description: "Fetch toxicity and hallucination content alerts",
  },
} as const;
