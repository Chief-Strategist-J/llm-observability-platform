export const COSTS_CONFIG_DEFAULTS = {
  DEFAULT_LOOKBACK_DAYS: 30,
  DEFAULT_SERVICE_SUB: "web-app-costs-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
} as const;
