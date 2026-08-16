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
} from '../../../types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../../../../shared/types/auth.types';

export class AuthInboundPortImplementation implements IAuthInboundPort {
  constructor(private readonly service: AuthService) {}

  createOrganization(input: CreateOrganizationInput): Promise<{ id: string; name: string; slug: string }> {
    return this.service.createOrganization(input);
  }

  deleteOrganization(orgId: string): Promise<void> {
    return this.service.deleteOrganization(orgId);
  }

  createUser(input: CreateUserInput): Promise<AuthUserRecord> {
    return this.service.createUser(input);
  }

  blockUser(userId: string): Promise<void> {
    return this.service.blockUser(userId);
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

  verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }> {
    return this.service.verifyApiKey(input);
  }

  fetchUserAuditLogs(userId: string): Promise<AuditLogRecord[]> {
    return this.service.fetchUserAuditLogs(userId);
  }

  getSystemPermissions(): string[] {
    return this.service.getSystemPermissions();
  }
}
