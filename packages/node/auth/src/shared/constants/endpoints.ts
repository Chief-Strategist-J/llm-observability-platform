export const AUTH_ENDPOINTS = {
  SIGN_UP: '/api/v1/auth/sign-up',
  SIGN_IN: '/api/v1/auth/sign-in',
  SESSION: '/api/v1/auth/session',
  FORGOT_PASSWORD: '/api/v1/auth/forgot-password',
  RESET_PASSWORD: '/api/v1/auth/reset-password',
  CHANGE_PASSWORD: '/api/v1/auth/change-password',
  API_KEYS: '/api/v1/auth/api-keys',
  API_KEYS_VERIFY: '/api/v1/auth/api-keys/verify',
  PERMISSIONS: '/api/v1/auth/permissions',
  AUDIT_LOGS: '/api/v1/auth/audit-logs',
  HEALTH: '/health',
} as const;

export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  PATCH: 'PATCH',
  DELETE: 'DELETE',
} as const;
