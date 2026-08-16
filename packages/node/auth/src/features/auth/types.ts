import { z } from 'zod';
import { UserRoleSchema } from '../../shared/types/auth.types';

export const SignInCredentialsSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});
export type SignInCredentials = z.infer<typeof SignInCredentialsSchema>;

export const AuthUserRecordSchema = z.object({
  id: z.string().min(1),
  email: z.string().email(),
  password_hash: z.string().min(1),
  name: z.string().min(1),
  org_id: z.string().min(1),
  org_name: z.string().min(1),
  role: UserRoleSchema,
});
export type AuthUserRecord = z.infer<typeof AuthUserRecordSchema>;

export const CreateApiKeyInputSchema = z.object({
  org_id: z.string().min(1),
  name: z.string().min(1),
});
export type CreateApiKeyInput = z.infer<typeof CreateApiKeyInputSchema>;
