import type { JsonMapOp } from './transform.types';

function coerceValue(value: unknown, to: 'string' | 'number' | 'boolean' | 'date'): unknown {
  switch (to) {
    case 'string':
      return String(value);
    case 'number':
      return Number(value);
    case 'boolean':
      return Boolean(value);
    case 'date':
      return new Date(value as string | number);
  }
}

export function mapJson(
  obj: Record<string, unknown>,
  ops: JsonMapOp[],
): Record<string, unknown> {
  let result = { ...obj };

  for (const op of ops) {
    switch (op.op) {
      case 'rename': {
        if (op.from in result) {
          result[op.to] = result[op.from];
          delete result[op.from];
        }
        break;
      }
      case 'pick': {
        const picked: Record<string, unknown> = {};
        for (const field of op.fields) {
          if (field in result) {
            picked[field] = result[field];
          }
        }
        result = picked;
        break;
      }
      case 'omit': {
        for (const field of op.fields) {
          delete result[field];
        }
        break;
      }
      case 'default': {
        if (!(op.field in result) || result[op.field] === undefined || result[op.field] === null) {
          result[op.field] = op.value;
        }
        break;
      }
      case 'coerce': {
        if (op.field in result) {
          result[op.field] = coerceValue(result[op.field], op.to);
        }
        break;
      }
    }
  }

  return result;
}
