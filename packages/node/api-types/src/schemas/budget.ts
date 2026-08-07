import { z } from 'zod';

export const BudgetSchema = z.object({
  id: z.string(),
  name: z.string(),
  limit_usd_micro: z.number(),
  spent_usd_micro: z.number(),
  start_date: z.string(),
  end_date: z.string(),
});

export type Budget = z.infer<typeof BudgetSchema>;
