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
} from '../../types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../../../shared/types/auth.types';

export interface IAuthInboundPort {
  createOrganization(input: CreateOrganizationInput): Promise<{ id: string; name: string; slug: string }>;
  deleteOrganization(orgId: string): Promise<void>;
  createUser(input: CreateUserInput): Promise<AuthUserRecord>;
  blockUser(userId: string): Promise<void>;
  deleteUser(userId: string): Promise<void>;
  signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  validateSession(token: string): Promise<AuthTokenPayload>;
  forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }>;
  resetPassword(input: ResetPasswordInput): Promise<void>;
  changePassword(userId: string, input: ChangePasswordInput): Promise<void>;
  generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }>;
  verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }>;
  fetchUserAuditLogs(userId: string): Promise<AuditLogRecord[]>;
  getSystemPermissions(): string[];
}
