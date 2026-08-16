import type { SignUpInput, SignInInput, ForgotPasswordInput, ResetPasswordInput, ChangePasswordInput, CreateApiKeyInput, VerifyApiKeyInput, AuthUserRecord } from '../../types';
import type { ApiKeyRecord, AuthTokenPayload } from '../../../../shared/types/auth.types';

export interface IAuthInboundPort {
  signUp(input: SignUpInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  signIn(input: SignInInput): Promise<{ token: string; payload: AuthTokenPayload; user: AuthUserRecord }>;
  validateSession(token: string): Promise<AuthTokenPayload>;
  forgotPassword(input: ForgotPasswordInput): Promise<{ resetToken: string }>;
  resetPassword(input: ResetPasswordInput): Promise<void>;
  changePassword(userId: string, input: ChangePasswordInput): Promise<void>;
  generateApiKey(input: CreateApiKeyInput): Promise<{ rawKey: string; keyRecord: ApiKeyRecord }>;
  verifyApiKey(input: VerifyApiKeyInput): Promise<{ valid: boolean; record: ApiKeyRecord; authorized: boolean }>;
  getSystemPermissions(): string[];
}
