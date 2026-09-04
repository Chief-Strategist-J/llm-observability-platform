export const QUALITY_CONFIG_DEFAULTS = {
  DEFAULT_MODEL: "gpt-4o",
  DEFAULT_TIME_RANGE: "24h",
  DEFAULT_LOOKBACK_DAYS: 7,
  DEFAULT_LIMIT: 20,
  DEFAULT_SLO_THRESHOLD_SCORE: 0.85,
  DEFAULT_SERVICE_SUB: "web-app-quality-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
  ERROR_FETCH_FAILED: "Failed to fetch quality evaluation metrics",
} as const;

export const QUALITY_EVENTS = {
  FETCHED: "quality.fetched",
  FAILED: "quality.failed",
} as const;

