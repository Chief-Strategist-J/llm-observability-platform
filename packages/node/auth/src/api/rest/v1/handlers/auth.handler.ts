import type { AuthService } from '../../../../features/auth/service';
import type { SignUpInput, SignInInput } from '../../../../features/auth/types';

export async function handleSignUp(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as SignUpInput;
  return service.signUp(input);
}

export async function handleSignIn(service: AuthService, body: unknown, headers?: Record<string, string>): Promise<unknown> {
  const input = body as SignInInput;
  const ipAddress = headers?.['x-forwarded-for'] ?? '127.0.0.1';
  const userAgent = headers?.['user-agent'] ?? 'unknown';
  return service.signIn({ ...input, ip_address: ipAddress, user_agent: userAgent });
}

export async function handleFetchAuditLogs(service: AuthService, userId: string): Promise<unknown> {
  return service.fetchUserAuditLogs(userId);
}
