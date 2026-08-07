import { z } from 'zod';

export const DateRangeSchema = z.object({
  from: z.string(),
  to: z.string(),
});

export type DateRange = z.infer<typeof DateRangeSchema>;

export const FilterStateSchema = z.object({
  dateRange: DateRangeSchema.optional(),
  model: z.string().optional(),
  service: z.string().optional(),
  environment: z.enum(['production', 'staging', 'development', 'all']).default('all'),
});

export type FilterState = z.infer<typeof FilterStateSchema>;
