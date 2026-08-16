import { z } from 'zod';
import {
  SignUpInputSchema,
  SignInInputSchema,
  AuthUserEntitySchema,
  AuditLogRecordSchema,
  ForgotPasswordInputSchema,
  ResetPasswordInputSchema,
  ChangePasswordInputSchema,
  CreateApiKeyInputSchema,
  VerifyApiKeyInputSchema,
  CreateOrganizationInputSchema,
  CreateUserInputSchema,
} from './schema/auth.schema';

export type CreateOrganizationInput = z.input<typeof CreateOrganizationInputSchema>;
export type CreateUserInput = z.input<typeof CreateUserInputSchema>;
export type SignUpInput = z.input<typeof SignUpInputSchema>;
export type SignInInput = z.input<typeof SignInInputSchema>;
export type AuthUserRecord = z.infer<typeof AuthUserEntitySchema>;
export type AuditLogRecord = z.infer<typeof AuditLogRecordSchema>;
export type ForgotPasswordInput = z.input<typeof ForgotPasswordInputSchema>;
export type ResetPasswordInput = z.input<typeof ResetPasswordInputSchema>;
export type ChangePasswordInput = z.input<typeof ChangePasswordInputSchema>;
export type CreateApiKeyInput = z.input<typeof CreateApiKeyInputSchema>;
export type VerifyApiKeyInput = z.input<typeof VerifyApiKeyInputSchema>;
