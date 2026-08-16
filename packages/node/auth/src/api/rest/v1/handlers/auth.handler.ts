import type { AuthService } from '../../../../features/auth/service';
import { SignInCredentialsSchema } from '../../../../features/auth/types';

export async function handleSignIn(service: AuthService, body: unknown): Promise<{ token: string; user: { id: string; email: string; org_id: string; role: string } }> {
  const parsed = SignInCredentialsSchema.parse(body);
  const { token, payload } = await service.signIn(parsed);

  return {
    token,
    user: {
      id: payload.sub,
      email: payload.email,
      org_id: payload.org.org_id,
      role: payload.org.role,
    },
  };
}
