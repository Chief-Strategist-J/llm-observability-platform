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
    super('Invalid email or password credentials', 'INVALID_CREDENTIALS', 401);
  }
}

export class UserBlockedError extends AuthError {
  constructor() {
    super('User account is blocked. Contact administrator.', 'USER_BLOCKED', 401);
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
    super('API key has been revoked or invalid', 'API_KEY_REVOKED', 401);
  }
}

export class UserAlreadyExistsError extends AuthError {
  constructor(email: string) {
    super(`Email address already registered: ${email}`, 'USER_ALREADY_EXISTS', 409);
  }
}

export class OrgAlreadyExistsError extends AuthError {
  constructor(name: string) {
    super(`Organization name already exists: ${name}`, 'ORG_ALREADY_EXISTS', 409);
  }
}

export class AccountLockedError extends AuthError {
  constructor() {
    super('Account locked due to consecutive failed login attempts', 'ACCOUNT_LOCKED', 429);
  }
}

export class InsufficientPermissionError extends AuthError {
  constructor(permission: string) {
    super(`Insufficient permission: key lacks ${permission}`, 'INSUFFICIENT_PERMISSION', 403);
  }
}

export class ValidationError extends AuthError {
  constructor(details: string) {
    super(`Validation failed: ${details}`, 'VALIDATION_ERROR', 400);
  }
}
