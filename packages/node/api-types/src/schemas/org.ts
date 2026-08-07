import { z } from 'zod';

export const OrgRoleSchema = z.enum(['owner', 'admin', 'member']);
export type OrgRole = z.infer<typeof OrgRoleSchema>;

export const OrgSchema = z.object({
  id: z.string(),
  name: z.string(),
  slug: z.string(),
  compliance_mode: z.enum(['standard', 'hipaa', 'eu_only']).default('standard'),
  plan: z.enum(['free', 'pro', 'enterprise']).default('free'),
});

export type Org = z.infer<typeof OrgSchema>;

export const OrgMemberSchema = z.object({
  id: z.string(),
  user_id: z.string(),
  org_id: z.string(),
  email: z.string().email(),
  name: z.string(),
  role: OrgRoleSchema,
  joined_at: z.string(),
});

export type OrgMember = z.infer<typeof OrgMemberSchema>;
