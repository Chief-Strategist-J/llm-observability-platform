export const QUALITY_CONFIG_DEFAULTS = {
  DEFAULT_LOOKBACK_DAYS: 7,
  DEFAULT_SLO_THRESHOLD_SCORE: 0.85,
  DEFAULT_SERVICE_SUB: "web-app-quality-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
} as const;
