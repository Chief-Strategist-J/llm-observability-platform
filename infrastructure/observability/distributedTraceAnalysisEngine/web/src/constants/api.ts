// API Configuration Constants
export const API_CONFIG = {
  BASE_URL: '/api/v1',
  HEALTH_URL: '/health',
  DEFAULT_LIMIT: 200,
  DEFAULT_OFFSET: 0,
  POLLING_INTERVAL_MS: 5000,
  TRACE_LIST_LIMIT: 100,
} as const;

// Anomaly Score Thresholds
export const ANOMALY_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.5,
  LOW: 0.3,
} as const;

// Colors for Anomaly Scores
export const ANOMALY_COLORS = {
  HIGH: '#dc2626',
  MEDIUM: '#f59e0b',
  LOW: '#10b981',
} as const;

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  NOT_FOUND: 404,
  BAD_REQUEST: 400,
  INTERNAL_ERROR: 500,
} as const;
