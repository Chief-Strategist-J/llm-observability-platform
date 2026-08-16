import { z } from 'zod';

export const AuthUserEntitySchema = z.object({
  id: z.string().min(1),
  email: z.string().email(),
  password_hash: z.string().min(1),
  name: z.string().min(1),
  org_id: z.string().min(1),
  org_name: z.string().min(1),
  role: z.string().min(1),
});

export const ApiKeyEntitySchema = z.object({
  key_id: z.string().min(1),
  org_id: z.string().min(1),
  key_hash: z.string().min(1),
  prefix: z.string().min(1),
  name: z.string().min(1),
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
