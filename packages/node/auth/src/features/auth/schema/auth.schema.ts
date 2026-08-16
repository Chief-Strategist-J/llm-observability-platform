import { z } from 'zod';
import { AUTH_CONSTANTS } from '../../../shared/constants/auth.constants';

export const UserRoleSchema = z.enum([
  AUTH_CONSTANTS.ROLE_ADMIN,
  AUTH_CONSTANTS.ROLE_MEMBER,
  AUTH_CONSTANTS.ROLE_VIEWER,
]);

export const ApiKeyTypeSchema = z.enum([
  AUTH_CONSTANTS.KEY_TYPE_GENERAL,
  AUTH_CONSTANTS.KEY_TYPE_TESTING,
  AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET,
]);

export const PasswordValidationSchema = z
  .string()
  .min(AUTH_CONSTANTS.PASSWORD_MIN_LENGTH)
  .regex(AUTH_CONSTANTS.PASSWORD_REGEX);

export const CreateOrganizationInputSchema = z.object({
  name: z.string().min(2),
  slug: z.string().optional(),
});

export const CreateUserInputSchema = z.object({
  email: z.string().email(),
  password: PasswordValidationSchema,
  name: z.string().min(2),
  org_id: z.string().min(1),
  role: UserRoleSchema.default(AUTH_CONSTANTS.ROLE_MEMBER),
  permissions: z.array(z.string()).default([]),
});

export const SignUpInputSchema = z.object({
  email: z.string().email().max(255),
  password: PasswordValidationSchema,
  name: z.string().min(2),
  organization_name: z.string().min(2),
  role: UserRoleSchema.default(AUTH_CONSTANTS.ROLE_ADMIN),
});

export const SignInInputSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
  ip_address: z.string().default('127.0.0.1'),
  user_agent: z.string().default('unknown'),
});

export const ForgotPasswordInputSchema = z.object({
  email: z.string().email(),
});

export const ResetPasswordInputSchema = z.object({
  token: z.string().min(1),
  new_password: PasswordValidationSchema,
});

export const ChangePasswordInputSchema = z.object({
  current_password: z.string().min(1),
  new_password: PasswordValidationSchema,
});

export const CreateApiKeyInputSchema = z.object({
  org_id: z.string().min(1),
  name: z.string().min(1),
  key_type: ApiKeyTypeSchema.default(AUTH_CONSTANTS.KEY_TYPE_GENERAL),
  permissions: z.array(z.string()).default([
    AUTH_CONSTANTS.PERMISSION_TRACES_READ,
    AUTH_CONSTANTS.PERMISSION_METRICS_READ,
    AUTH_CONSTANTS.PERMISSION_LOGS_READ,
  ]),
});

export const VerifyApiKeyInputSchema = z.object({
  key: z.string().min(1),
  required_permission: z.string().optional(),
});

export const AuditLogRecordSchema = z.object({
  id: z.string().min(1),
  user_id: z.string().min(1),
  org_id: z.string().min(1),
  event_type: z.string().min(1),
  ip_address: z.string().min(1),
  user_agent: z.string().min(1),
  timestamp_ms: z.number().int().positive(),
});

export const AuthUserEntitySchema = z.object({
  id: z.string().min(1),
  email: z.string().email(),
  password_hash: z.string().min(1),
  name: z.string().min(1),
  org_id: z.string().min(1),
  org_name: z.string().min(1),
  role: UserRoleSchema,
  blocked: z.boolean().default(false),
  user_permissions: z.array(z.string()).default([]),
});

export const ApiKeyEntitySchema = z.object({
  key_id: z.string().min(1),
  org_id: z.string().min(1),
  key_type: ApiKeyTypeSchema,
  key_hash: z.string().min(1),
  prefix: z.string().min(1),
  name: z.string().min(1),
  permissions: z.array(z.string()),
  created_at_ms: z.number().int().positive(),
  revoked: z.boolean(),
});

export const AUTH_JSON_MAPPING = {
  fromApi: [
    { op: 'rename', from: 'emailAddress', to: 'email' },
    { op: 'rename', from: 'organizationId', to: 'org_id' },
    { op: 'rename', from: 'organizationName', to: 'org_name' },
  ],
  toApi: [
    { op: 'rename', from: 'email', to: 'emailAddress' },
    { op: 'rename', from: 'org_id', to: 'organizationId' },
    { op: 'rename', from: 'org_name', to: 'organizationName' },
  ],
} as const;
