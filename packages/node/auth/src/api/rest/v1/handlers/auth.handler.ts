import type { AuthService } from '../../../../features/auth/service';
import type { SignUpInput, SignInInput, CreateOrganizationInput, CreateUserInput } from '../../../../features/auth/types';

export async function handleCreateOrganization(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as CreateOrganizationInput;
  return service.createOrganization(input);
}

export async function handleDeleteOrganization(service: AuthService, orgId: string): Promise<unknown> {
  await service.deleteOrganization(orgId);
  return { success: true, message: `Organization ${orgId} and all associated entity details soft-deleted with 30-day backup retention.` };
}

export async function handleCreateUser(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as CreateUserInput;
  return service.createUser(input);
}

export async function handleBlockUser(service: AuthService, userId: string): Promise<unknown> {
  await service.blockUser(userId);
  return { success: true, message: `User ${userId} blocked successfully.` };
}

export async function handleDeleteUser(service: AuthService, userId: string): Promise<unknown> {
  await service.deleteUser(userId);
  return { success: true, message: `User ${userId} soft-deleted with 30-day backup retention.` };
}

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
