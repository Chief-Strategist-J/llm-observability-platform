import type { AuthService } from '../../../../features/auth/service';
import type { SignUpInput, SignInInput, CreateOrganizationInput, CreateUserInput, UpdateUserProfileInput, InviteUserInput, UpdateUserRoleInput, UpdateUserPermissionsInput, UpdateOrganizationInput, AuditLogFilter } from '../../../../features/auth/types';

export async function handleListOrganizations(service: AuthService, userId: string): Promise<unknown> {
  return service.listOrganizations(userId);
}

export async function handleGetOrganization(service: AuthService, orgId: string): Promise<unknown> {
  return service.getOrganization(orgId);
}

export async function handleCreateOrganization(service: AuthService, body: unknown, creatorUserId?: string): Promise<unknown> {
  const input = body as CreateOrganizationInput;
  return service.createOrganization(input, creatorUserId);
}

export async function handleUpdateOrganization(service: AuthService, orgId: string, body: unknown): Promise<unknown> {
  const input = body as UpdateOrganizationInput;
  return service.updateOrganization(orgId, input);
}

export async function handleDeleteOrganization(service: AuthService, orgId: string): Promise<unknown> {
  await service.deleteOrganization(orgId);
  return { success: true, message: `Organization ${orgId} and all associated entity details soft-deleted with 30-day backup retention.` };
}

export async function handleSwitchOrganization(service: AuthService, userId: string, targetOrgId: string, currentToken: string): Promise<unknown> {
  return service.switchOrganization(userId, targetOrgId, currentToken);
}

export async function handleListUsers(service: AuthService, orgId: string): Promise<unknown> {
  return service.listUsers(orgId);
}

export async function handleGetUserById(service: AuthService, userId: string): Promise<unknown> {
  return service.getUserById(userId);
}

export async function handleGetMyProfile(service: AuthService, userId: string): Promise<unknown> {
  return service.getMyProfile(userId);
}

export async function handleUpdateMyProfile(service: AuthService, userId: string, body: unknown): Promise<unknown> {
  const input = body as UpdateUserProfileInput;
  return service.updateMyProfile(userId, input);
}

export async function handleInviteUser(service: AuthService, body: unknown, orgId: string, orgName: string): Promise<unknown> {
  const input = body as InviteUserInput;
  return service.inviteUser(input, orgId, orgName);
}

export async function handleUpdateUserRole(service: AuthService, userId: string, body: unknown): Promise<void> {
  const input = body as UpdateUserRoleInput;
  return service.updateUserRole(userId, input);
}

export async function handleGetUserPermissions(service: AuthService, userId: string): Promise<unknown> {
  return service.getUserPermissions(userId);
}

export async function handleUpdateUserPermissions(service: AuthService, userId: string, body: unknown): Promise<void> {
  const input = body as UpdateUserPermissionsInput;
  return service.updateUserPermissions(userId, input);
}

export async function handleCreateUser(service: AuthService, body: unknown): Promise<unknown> {
  const input = body as CreateUserInput;
  return service.createUser(input);
}

export async function handleBlockUser(service: AuthService, userId: string): Promise<unknown> {
  await service.blockUser(userId);
  return { success: true, message: `User ${userId} blocked successfully.` };
}

export async function handleUnblockUser(service: AuthService, userId: string): Promise<unknown> {
  await service.unblockUser(userId);
  return { success: true, message: `User ${userId} unblocked successfully.` };
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

export async function handleSignOut(service: AuthService, authHeader?: string): Promise<void> {
  const token = authHeader?.replace('Bearer ', '') ?? '';
  return service.signOut(token);
}

export async function handleListApiKeys(service: AuthService, orgId: string): Promise<unknown> {
  return service.listApiKeys(orgId);
}

export async function handleRevokeApiKey(service: AuthService, keyId: string): Promise<void> {
  return service.revokeApiKey(keyId);
}

export async function handleFetchAuditLogs(service: AuthService, userId: string, queryParams?: Record<string, string>): Promise<unknown> {
  const filters: AuditLogFilter | undefined = queryParams
    ? {
        event_type: queryParams['event_type'],
        from: queryParams['from'],
        to: queryParams['to'],
      }
    : undefined;
  return service.fetchUserAuditLogs(userId, filters);
}
