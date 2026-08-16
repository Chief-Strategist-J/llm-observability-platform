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
} from '../../types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../../../shared/types/auth.types';
import type { OrganizationRecord } from '../../repository';

export interface IAuthInboundPort {
  listOrganizations(userId: string): Promise<OrganizationRecord[]>;
  getOrganization(orgId: string): Promise<OrganizationRecord>;
  createOrganization(input: CreateOrganizationInput, creatorUserId?: string): Promise<{ id: string; name: string; slug: string }>;
  updateOrganization(orgId: string, input: UpdateOrganizationInput): Promise<OrganizationRecord>;
  deleteOrganization(orgId: string): Promise<void>;
  switchOrganization(userId: string, targetOrgId: string, currentToken: string): Promise<{ token: string; payload: AuthTokenPayload }>;
  listUsers(orgId: string): Promise<AuthUserRecord[]>;
  getUserById(userId: string): Promise<AuthUserRecord>;
  getMyProfile(userId: string): Promise<AuthUserRecord>;
  updateMyProfile(userId: string, input: UpdateUserProfileInput): Promise<AuthUserRecord>;
  inviteUser(input: InviteUserInput, orgId: string, orgName: string): Promise<AuthUserRecord>;
  updateUserRole(userId: string, input: UpdateUserRoleInput): Promise<void>;
  getUserPermissions(userId: string): Promise<string[]>;
  updateUserPermissions(userId: string, input: UpdateUserPermissionsInput): Promise<void>;
  createUser(input: CreateUserInput): Promise<AuthUserRecord>;
  blockUser(userId: string): Promise<void>;
  unblockUser(userId: string): Promise<void>;
  deleteUser(userId: string): Promise<void>;
  signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  signOut(token: string): Promise<void>;
  validateSession(token: string): Promise<AuthTokenPayload>;
  forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }>;
  resetPassword(input: ResetPasswordInput): Promise<void>;
  changePassword(userId: string, input: ChangePasswordInput): Promise<void>;
  generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }>;
  listApiKeys(orgId: string): Promise<ApiKeyRecord[]>;
  verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }>;
  revokeApiKey(keyId: string): Promise<void>;
  fetchUserAuditLogs(userId: string, filters?: AuditLogFilter): Promise<AuditLogRecord[]>;
  getSystemPermissions(): string[];
}
