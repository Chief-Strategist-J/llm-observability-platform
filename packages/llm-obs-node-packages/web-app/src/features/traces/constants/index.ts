export * from './traces.text';
export * from './traces.telemetry';

export const TRACES_CONFIG_DEFAULTS = {
  DEFAULT_PAGE_SIZE: 20,
  DEFAULT_SERVICE_SUB: "web-app-traces-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  DEFAULT_JWT_EXPIRY_SECONDS: 3600,
  DEFAULT_ENGINE_URL: "http://localhost:8000",
  ERROR_FETCH_TRACES: "Failed to fetch distributed traces",
  ERROR_FETCH_DETAIL: "Failed to fetch trace detail",
} as const;

export const TRACES_ENDPOINTS = {
  LIST: "/api/v1/traces/list",
  DETAIL: "/api/v1/traces",
} as const;

export const TRACES_EVENTS = {
  FETCHED: "traces.fetched",
  FAILED: "traces.failed",
  DETAIL_FETCHED: "trace_detail.fetched",
  DETAIL_FAILED: "trace_detail.failed",
} as const;

