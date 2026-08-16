import type { AuthService } from '../../../../features/auth/service';
import type { AuthTokenPayload } from '../../../../shared/types/auth.types';
import { AUTH_CONSTANTS } from '../../../../shared/constants/auth.constants';

export async function handleVerifySession(service: AuthService, authorizationHeader?: string): Promise<AuthTokenPayload> {
  if (!authorizationHeader || !authorizationHeader.startsWith(AUTH_CONSTANTS.BEARER_PREFIX)) {
    throw new Error('Missing or invalid Authorization header');
  }

  const token = authorizationHeader.substring(AUTH_CONSTANTS.BEARER_PREFIX.length);
  return service.validateSession(token);
}
