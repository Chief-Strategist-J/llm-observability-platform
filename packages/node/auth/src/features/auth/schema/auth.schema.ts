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
  .string({ invalid_type_error: 'Password must be a string' })
  .min(
    AUTH_CONSTANTS.SECURITY_CONFIG.PASSWORD_MIN_LENGTH,
    `Password must be at least ${AUTH_CONSTANTS.SECURITY_CONFIG.PASSWORD_MIN_LENGTH} characters long`
  )
  .regex(
    new RegExp(AUTH_CONSTANTS.SECURITY_CONFIG.PASSWORD_PATTERN),
    'Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character (!@#$%^&*)'
  );

export const CreateOrganizationInputSchema = z.object({
  name: z.string().min(2, 'Organization name must be at least 2 characters long'),
  slug: z.string().optional(),
});

export const CreateUserInputSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: PasswordValidationSchema,
  name: z.string().min(2, 'Full name must be at least 2 characters long'),
  org_id: z.string().min(1, 'Target organization ID is required'),
  role: UserRoleSchema.default(AUTH_CONSTANTS.ROLE_MEMBER),
  permissions: z.array(z.string()).default([]),
});

export const SignUpInputSchema = z.object({
  email: z.string().email('Please enter a valid email address').max(255),
  password: PasswordValidationSchema,
  name: z.string().min(2, 'Full name must be at least 2 characters long'),
  organization_name: z.string().min(2, 'Organization name must be at least 2 characters long'),
  role: UserRoleSchema.default(AUTH_CONSTANTS.ROLE_ADMIN),
});

export const SignInInputSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  ip_address: z.string().default('127.0.0.1'),
  user_agent: z.string().default('unknown'),
});

export const ForgotPasswordInputSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
});

export const ResetPasswordInputSchema = z.object({
  token: z.string().min(1, 'Reset token is required'),
  new_password: PasswordValidationSchema,
});

export const ChangePasswordInputSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: PasswordValidationSchema,
});

export const CreateApiKeyInputSchema = z.object({
  org_id: z.string().min(1, 'Organization ID is required'),
  name: z.string().min(1, 'Key name is required'),
  key_type: ApiKeyTypeSchema.default(AUTH_CONSTANTS.KEY_TYPE_GENERAL),
  permissions: z.array(z.string()).default([
    AUTH_CONSTANTS.PERMISSION_TRACES_READ,
    AUTH_CONSTANTS.PERMISSION_METRICS_READ,
    AUTH_CONSTANTS.PERMISSION_LOGS_READ,
  ]),
});

export const VerifyApiKeyInputSchema = z.object({
  key: z.string().min(1, 'API key string is required'),
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
