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
} from './schema/auth.schema';

export type SignUpInput = z.infer<typeof SignUpInputSchema>;
export type SignInInput = z.infer<typeof SignInInputSchema>;
export type AuthUserRecord = z.infer<typeof AuthUserEntitySchema>;
export type AuditLogRecord = z.infer<typeof AuditLogRecordSchema>;
export type ForgotPasswordInput = z.infer<typeof ForgotPasswordInputSchema>;
export type ResetPasswordInput = z.infer<typeof ResetPasswordInputSchema>;
export type ChangePasswordInput = z.infer<typeof ChangePasswordInputSchema>;
export type CreateApiKeyInput = z.infer<typeof CreateApiKeyInputSchema>;
export type VerifyApiKeyInput = z.infer<typeof VerifyApiKeyInputSchema>;
