import type { AuthService } from '../../../../features/auth/service';
import type { AuthTokenPayload } from '../../../../shared/types/auth.types';

export async function handleVerifySession(service: AuthService, authorizationHeader?: string): Promise<AuthTokenPayload> {
  if (!authorizationHeader || !authorizationHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid Authorization header');
  }

  const token = authorizationHeader.substring(7);
  return service.validateSession(token);
}
