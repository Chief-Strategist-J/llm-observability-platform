export const AUTH_ENDPOINTS = {
  SIGN_IN: '/api/v1/auth/sign-in',
  SESSION: '/api/v1/auth/session',
  API_KEYS: '/api/v1/auth/api-keys',
  API_KEYS_VERIFY: '/api/v1/auth/api-keys/verify',
  HEALTH: '/health',
} as const;

export const HTTP_METHODS = {
  GET: 'GET',
  POST: 'POST',
  PUT: 'PUT',
  PATCH: 'PATCH',
  DELETE: 'DELETE',
} as const;
