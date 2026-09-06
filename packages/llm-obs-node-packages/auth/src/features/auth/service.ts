import type { AuthRepositoryPort, OrganizationRecord } from './repository';
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
} from './types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../shared/types/auth.types';
import type { AuthEventProducer } from '../../shared/messaging/producers/auth-event.producer';

import { OrganizationDomainService } from './services/organization.service';
import { UserManagementDomainService } from './services/user-management.service';
import { UserAuthDomainService } from './services/user-auth.service';
import { PasswordDomainService } from './services/password.service';
import { ApiKeyDomainService } from './services/api-key.service';
import { AuditLogDomainService } from './services/audit-log.service';

export class AuthService {
  private readonly orgService: OrganizationDomainService;
  private readonly userService: UserManagementDomainService;
  private readonly authService: UserAuthDomainService;
  private readonly passwordService: PasswordDomainService;
  private readonly apiKeyService: ApiKeyDomainService;
  private readonly auditLogService: AuditLogDomainService;

  constructor(
    repo: AuthRepositoryPort,
    eventProducer?: AuthEventProducer,
  ) {
    this.orgService = new OrganizationDomainService(repo);
    this.userService = new UserManagementDomainService(repo);
    this.authService = new UserAuthDomainService(repo, eventProducer);
    this.passwordService = new PasswordDomainService(repo);
    this.apiKeyService = new ApiKeyDomainService(repo);
    this.auditLogService = new AuditLogDomainService(repo);
  }

  async listOrganizations(userId: string): Promise<OrganizationRecord[]> {
    return this.orgService.listOrganizations(userId);
  }

  async getOrganization(orgId: string): Promise<OrganizationRecord> {
    return this.orgService.getOrganization(orgId);
  }

  async createOrganization(input: CreateOrganizationInput, creatorUserId?: string): Promise<{ id: string; name: string; slug: string }> {
    return this.orgService.createOrganization(input, creatorUserId);
  }

  async updateOrganization(orgId: string, input: UpdateOrganizationInput): Promise<OrganizationRecord> {
    return this.orgService.updateOrganization(orgId, input);
  }

  async deleteOrganization(orgId: string): Promise<void> {
    return this.orgService.deleteOrganization(orgId);
  }

  async switchOrganization(userId: string, targetOrgId: string, currentToken: string): Promise<{ token: string; payload: AuthTokenPayload }> {
    return this.orgService.switchOrganization(userId, targetOrgId, currentToken);
  }

  async listUsers(orgId: string): Promise<AuthUserRecord[]> {
    return this.userService.listUsers(orgId);
  }

  async getUserById(userId: string): Promise<AuthUserRecord> {
    return this.userService.getUserById(userId);
  }

  async getMyProfile(userId: string): Promise<AuthUserRecord> {
    return this.userService.getMyProfile(userId);
  }

  async updateMyProfile(userId: string, input: UpdateUserProfileInput): Promise<AuthUserRecord> {
    return this.userService.updateMyProfile(userId, input);
  }

  async inviteUser(input: InviteUserInput, orgId: string, orgName: string): Promise<AuthUserRecord> {
    return this.userService.inviteUser(input, orgId, orgName);
  }

  async updateUserRole(userId: string, input: UpdateUserRoleInput): Promise<void> {
    return this.userService.updateUserRole(userId, input);
  }

  async getUserPermissions(userId: string): Promise<string[]> {
    return this.userService.getUserPermissions(userId);
  }

  async updateUserPermissions(userId: string, input: UpdateUserPermissionsInput): Promise<void> {
    return this.userService.updateUserPermissions(userId, input);
  }

  async createUser(input: CreateUserInput): Promise<AuthUserRecord> {
    return this.userService.createUser(input);
  }

  async blockUser(userId: string): Promise<void> {
    return this.userService.blockUser(userId);
  }

  async unblockUser(userId: string): Promise<void> {
    return this.userService.unblockUser(userId);
  }

  async deleteUser(userId: string): Promise<void> {
    return this.userService.deleteUser(userId);
  }

  async signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    return this.authService.signUp(input);
  }

  async signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }> {
    return this.authService.signIn(input);
  }

  async signOut(token: string): Promise<void> {
    return this.authService.signOut(token);
  }

  async validateSession(token: string): Promise<AuthTokenPayload> {
    return this.authService.validateSession(token);
  }

  async forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }> {
    return this.passwordService.forgotPassword(input);
  }

  async resetPassword(input: ResetPasswordInput): Promise<void> {
    return this.passwordService.resetPassword(input);
  }

  async changePassword(userId: string, input: ChangePasswordInput): Promise<void> {
    return this.passwordService.changePassword(userId, input);
  }

  async generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }> {
    return this.apiKeyService.generateApiKey(input);
  }

  async listApiKeys(orgId: string): Promise<ApiKeyRecord[]> {
    return this.apiKeyService.listApiKeys(orgId);
  }

  async verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }> {
    return this.apiKeyService.verifyApiKey(input);
  }

  async revokeApiKey(keyId: string): Promise<void> {
    return this.apiKeyService.revokeApiKey(keyId);
  }

  async fetchUserAuditLogs(userId: string, filters?: AuditLogFilter): Promise<AuditLogRecord[]> {
    return this.auditLogService.fetchUserAuditLogs(userId, filters);
  }

  async purgeExpiredSoftDeletes(): Promise<number> {
    return this.auditLogService.purgeExpiredSoftDeletes();
  }

  getSystemPermissions(): string[] {
    return this.apiKeyService.getSystemPermissions();
  }
}
