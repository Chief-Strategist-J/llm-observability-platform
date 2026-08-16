export class AuthError extends Error {
  readonly code: string;
  readonly statusCode: number;

  constructor(message: string, code: string, statusCode = 401) {
    super(message);
    this.name = 'AuthError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

export class InvalidCredentialsError extends AuthError {
  constructor() {
    super('Invalid email or password', 'INVALID_CREDENTIALS', 401);
  }
}

export class TokenExpiredError extends AuthError {
  constructor() {
    super('Authentication token has expired', 'TOKEN_EXPIRED', 401);
  }
}

export class ForbiddenRoleError extends AuthError {
  constructor(requiredRole: string) {
    super(`Requires ${requiredRole} role access`, 'FORBIDDEN_ROLE', 403);
  }
}

export class ApiKeyRevokedError extends AuthError {
  constructor() {
    super('API key has been revoked', 'API_KEY_REVOKED', 401);
  }
}
