import type { IAuthInboundPort } from '../auth-inbound.port';
import type { AuthService } from '../../../service';
import type {
  SignUpInput,
  SignInInput,
  ForgotPasswordInput,
  ResetPasswordInput,
  ChangePasswordInput,
  CreateApiKeyInput,
  VerifyApiKeyInput,
  CreateOrganizationInput,
  CreateUserInput,
  AuthUserRecord,
  AuditLogRecord,
  UpdateUserProfileInput,
  InviteUserInput,
  UpdateUserRoleInput,
  UpdateUserPermissionsInput,
  UpdateOrganizationInput,
  AuditLogFilter,
} from '../../../types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../../../../shared/types/auth.types';
import type { OrganizationRecord } from '../../../repository';

export class AuthInboundPortImplementation implements IAuthInboundPort {
  constructor(private readonly service: AuthService) {}

  listOrganizations(userId: string): Promise<OrganizationRecord[]> {
    return this.service.listOrganizations(userId);
  }

  getOrganization(orgId: string): Promise<OrganizationRecord> {
    return this.service.getOrganization(orgId);
  }

  createOrganization(input: CreateOrganizationInput): Promise<{ id: string; name: string; slug: string }> {
    return this.service.createOrganization(input);
  }

  updateOrganization(orgId: string, input: UpdateOrganizationInput): Promise<OrganizationRecord> {
    return this.service.updateOrganization(orgId, input);
  }

  deleteOrganization(orgId: string): Promise<void> {
    return this.service.deleteOrganization(orgId);
  }

  switchOrganization(userId: string, targetOrgId: string, currentToken: string): Promise<{ token: string; payload: AuthTokenPayload }> {
    return this.service.switchOrganization(userId, targetOrgId, currentToken);
  }

  listUsers(orgId: string): Promise<AuthUserRecord[]> {
    return this.service.listUsers(orgId);
  }

  getUserById(userId: string): Promise<AuthUserRecord> {
    return this.service.getUserById(userId);
  }

  getMyProfile(userId: string): Promise<AuthUserRecord> {
    return this.service.getMyProfile(userId);
  }

  updateMyProfile(userId: string, input: UpdateUserProfileInput): Promise<AuthUserRecord> {
    return this.service.updateMyProfile(userId, input);
  }

  inviteUser(input: InviteUserInput, orgId: string, orgName: string): Promise<AuthUserRecord> {
    return this.service.inviteUser(input, orgId, orgName);
  }

  updateUserRole(userId: string, input: UpdateUserRoleInput): Promise<void> {
    return this.service.updateUserRole(userId, input);
  }

  getUserPermissions(userId: string): Promise<string[]> {
    return this.service.getUserPermissions(userId);
  }

  updateUserPermissions(userId: string, input: UpdateUserPermissionsInput): Promise<void> {
    return this.service.updateUserPermissions(userId, input);
  }

  createUser(input: CreateUserInput): Promise<AuthUserRecord> {
    return this.service.createUser(input);
  }

  blockUser(userId: string): Promise<void> {
    return this.service.blockUser(userId);
  }

  unblockUser(userId: string): Promise<void> {
    return this.service.unblockUser(userId);
  }

  deleteUser(userId: string): Promise<void> {
    return this.service.deleteUser(userId);
  }

  signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    return this.service.signUp(input);
  }

  signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    return this.service.signIn(input);
  }

  signOut(token: string): Promise<void> {
    return this.service.signOut(token);
  }

  validateSession(token: string): Promise<AuthTokenPayload> {
    return this.service.validateSession(token);
  }

  forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }> {
    return this.service.forgotPassword(input);
  }

  resetPassword(input: ResetPasswordInput): Promise<void> {
    return this.service.resetPassword(input);
  }

  changePassword(userId: string, input: ChangePasswordInput): Promise<void> {
    return this.service.changePassword(userId, input);
  }

  generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
    return this.service.generateApiKey(input);
  }

  listApiKeys(orgId: string): Promise<ApiKeyRecord[]> {
    return this.service.listApiKeys(orgId);
  }

  verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }> {
    return this.service.verifyApiKey(input);
  }

  revokeApiKey(keyId: string): Promise<void> {
    return this.service.revokeApiKey(keyId);
  }

  fetchUserAuditLogs(userId: string, filters?: AuditLogFilter): Promise<AuditLogRecord[]> {
    return this.service.fetchUserAuditLogs(userId, filters);
  }

  getSystemPermissions(): string[] {
    return this.service.getSystemPermissions();
  }
}
