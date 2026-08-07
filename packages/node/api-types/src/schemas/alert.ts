import { z } from 'zod';

export const AlertSchema = z.object({
  id: z.string(),
  title: z.string(),
  severity: z.enum(['good', 'warn', 'bad']),
  active: z.boolean(),
  triggered_at: z.string(),
});

export type Alert = z.infer<typeof AlertSchema>;
