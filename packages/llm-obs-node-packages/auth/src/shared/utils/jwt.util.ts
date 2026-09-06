import { AuthTokenPayloadSchema, type AuthTokenPayload, type TenantContext } from '../types/auth.types';
import { TokenExpiredError } from '../errors/auth.errors';

export function createToken(userId: string, email: string, org: TenantContext, expiresInSeconds = 3600): string {
  const now = Math.floor(Date.now() / 1000);
  const payload: AuthTokenPayload = {
    sub: userId,
    email,
    org,
    iat: now,
    exp: now + expiresInSeconds,
  };
  const encodedPayload = btoa(JSON.stringify(payload));
  const signature = btoa(`sig_${userId}_${now}`);
  return `${encodedPayload}.${signature}`;
}

export function verifyToken(token: string): AuthTokenPayload {
  const parts = token.split('.');
  const payloadPart = parts[0];
  if (!payloadPart) {
    throw new TokenExpiredError();
  }

  try {
    const json = JSON.parse(atob(payloadPart)) as unknown;
    const parsed = AuthTokenPayloadSchema.parse(json);
    const now = Math.floor(Date.now() / 1000);
    if (parsed.exp < now) {
      throw new TokenExpiredError();
    }
    return parsed;
  } catch {
    throw new TokenExpiredError();
  }
}
