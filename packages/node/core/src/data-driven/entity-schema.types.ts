import type { z } from 'zod';
import type { JsonMapOp } from './transform.types';

export type FieldKind = 'text' | 'number' | 'select' | 'date' | 'boolean';

export interface FieldConfig<T = unknown> {
  key: string;
  label: string;
  kind: FieldKind;
  required?: boolean;
  options?: { label: string; value: T }[];
  defaultValue?: T;
}

export interface EntitySchema<T = Record<string, unknown>> {
  name: string;
  endpoint: string;
  fields: FieldConfig[];
  validate: z.ZodType<T>;
  fromApi?: JsonMapOp[];
  toApi?: JsonMapOp[];
}
