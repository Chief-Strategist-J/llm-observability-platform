import { z } from 'zod';

export const UserRoleSchema = z.enum(['admin', 'engineer', 'viewer']);
export type UserRole = z.infer<typeof UserRoleSchema>;

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
  key_hash: z.string().min(1),
  prefix: z.string().min(1),
  name: z.string().min(1),
  created_at_ms: z.number().positive(),
  revoked: z.boolean(),
});
export type ApiKeyRecord = z.infer<typeof ApiKeyRecordSchema>;
