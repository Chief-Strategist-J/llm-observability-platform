export const TRACES_CONFIG_DEFAULTS = {
  DEFAULT_PAGE_SIZE: 20,
  DEFAULT_SERVICE_SUB: "web-app-traces-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
} as const;

export const TRACES_ENDPOINTS = {
  LIST: "/api/v1/traces/list",
  DETAIL: "/api/v1/traces",
} as const;
