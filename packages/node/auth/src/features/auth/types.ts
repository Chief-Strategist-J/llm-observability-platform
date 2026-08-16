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
  UpdateUserProfileInputSchema,
  InviteUserInputSchema,
  UpdateUserRoleInputSchema,
  UpdateUserPermissionsInputSchema,
  UpdateOrganizationInputSchema,
  AuditLogFilterSchema,
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
export type UpdateUserProfileInput = z.input<typeof UpdateUserProfileInputSchema>;
export type InviteUserInput = z.input<typeof InviteUserInputSchema>;
export type UpdateUserRoleInput = z.input<typeof UpdateUserRoleInputSchema>;
export type UpdateUserPermissionsInput = z.input<typeof UpdateUserPermissionsInputSchema>;
export type UpdateOrganizationInput = z.input<typeof UpdateOrganizationInputSchema>;
export type AuditLogFilter = z.input<typeof AuditLogFilterSchema>;
