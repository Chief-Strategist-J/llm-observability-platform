export const LATENCY_CONFIG_DEFAULTS = {
  DEFAULT_QUANTILES: "0.50,0.95,0.99",
  DEFAULT_LOOKBACK_DAYS: 7,
  DEFAULT_TIME_WINDOW: "1h",
  DEFAULT_MODEL_ALL: "all",
  DEFAULT_ENGINE_URL: "http://localhost:8003",
  DEFAULT_JWT_SECRET: "dev-secret-key-change-in-production",
  DEFAULT_SERVICE_SUB: "nextjs-web-app",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
} as const;

export const LATENCY_ENDPOINTS = {
  PERCENTILES: "/v1/latency/percentiles",
  SLO: "/v1/latency/slo",
  BASELINE: "/v1/latency/baseline",
  ATTRIBUTION: "/v1/latency/attribution",
} as const;
