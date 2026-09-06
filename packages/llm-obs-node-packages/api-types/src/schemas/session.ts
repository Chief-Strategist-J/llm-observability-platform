import { z } from 'zod';
import { OrgRoleSchema } from './org.js';

export const SessionUserSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  name: z.string(),
  image: z.string().optional(),
});

export type SessionUser = z.infer<typeof SessionUserSchema>;

export const OrgSessionSchema = z.object({
  user: SessionUserSchema,
  org: z.object({
    id: z.string(),
    name: z.string(),
    role: OrgRoleSchema,
  }),
  expires: z.string(),
});

export type OrgSession = z.infer<typeof OrgSessionSchema>;
