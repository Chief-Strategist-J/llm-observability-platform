export const OVERVIEW_CONFIG_DEFAULTS = {
  DEFAULT_LOOKBACK_HOURS: 24,
  DEFAULT_TIME_RANGE: "24h",
  DEFAULT_SERVICE_SUB: "web-app-overview-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
  ERROR_FETCH_FAILED: "Failed to fetch overview summary",
} as const;

export const OVERVIEW_ENDPOINTS = {
  SUMMARY: "/api/v1/overview/summary",
  HEALTH: "/api/v1/overview/health",
  RECENT_TRACES: "/api/v1/overview/recent-traces",
} as const;

export const OVERVIEW_EVENTS = {
  FETCHED: "overview.fetched",
  FAILED: "overview.failed",
} as const;

