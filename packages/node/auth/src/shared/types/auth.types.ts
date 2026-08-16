import { z } from 'zod';
import { AUTH_CONSTANTS } from '../constants/auth.constants';

export const UserRoleSchema = z.enum([
  AUTH_CONSTANTS.ROLE_ADMIN,
  AUTH_CONSTANTS.ROLE_MEMBER,
  AUTH_CONSTANTS.ROLE_VIEWER,
]);
export type UserRole = z.infer<typeof UserRoleSchema>;

export const ApiKeyTypeSchema = z.enum([
  AUTH_CONSTANTS.KEY_TYPE_GENERAL,
  AUTH_CONSTANTS.KEY_TYPE_TESTING,
  AUTH_CONSTANTS.KEY_TYPE_SUPER_SECRET,
]);
export type ApiKeyType = z.infer<typeof ApiKeyTypeSchema>;

export const TenantContextSchema = z.object({
  org_id: z.string().min(1),
  org_name: z.string().min(1),
  role: UserRoleSchema,
});
export type TenantContext = z.infer<typeof TenantContextSchema>;

export const AuthTokenPayloadSchema = z.object({
  sub: z.string().min(1),
  email: z.string().email(),
  org: TenantContextSchema,
  exp: z.number().positive(),
  iat: z.number().positive(),
});
export type AuthTokenPayload = z.infer<typeof AuthTokenPayloadSchema>;

export const ApiKeyRecordSchema = z.object({
  key_id: z.string().min(1),
  org_id: z.string().min(1),
  key_type: ApiKeyTypeSchema,
  key_hash: z.string().min(1),
  prefix: z.string().min(1),
  name: z.string().min(1),
  permissions: z.array(z.string()),
  created_at_ms: z.number().positive(),
  revoked: z.boolean(),
});
export type ApiKeyRecord = z.infer<typeof ApiKeyRecordSchema>;
