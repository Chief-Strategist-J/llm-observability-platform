import type { JsonMapOp } from './transform.types';
import { JsonMapOpKind, CoerceTarget } from './transform.types';

function coerceValue(value: unknown, to: CoerceTarget | `${CoerceTarget}`): unknown {
  switch (to) {
    case CoerceTarget.STRING:
      return String(value);
    case CoerceTarget.NUMBER:
      return Number(value);
    case CoerceTarget.BOOLEAN:
      return Boolean(value);
    case CoerceTarget.DATE:
      return new Date(value as string | number);
    default:
      return value;
  }
}

export function mapJson(
  obj: Record<string, unknown>,
  ops: JsonMapOp[],
): Record<string, unknown> {
  let result = { ...obj };

  for (const op of ops) {
    switch (op.op) {
      case JsonMapOpKind.RENAME: {
        if (op.from in result) {
          result[op.to] = result[op.from];
          delete result[op.from];
        }
        break;
      }
      case JsonMapOpKind.PICK: {
        const picked: Record<string, unknown> = {};
        const keys = 'keys' in op && Array.isArray(op.keys) ? op.keys : ('fields' in op && Array.isArray(op.fields) ? op.fields : []);
        for (const k of keys) {
          if (k in result) {
            picked[k] = result[k];
          }
        }
        result = picked;
        break;
      }
      case JsonMapOpKind.OMIT: {
        const keys = 'keys' in op && Array.isArray(op.keys) ? op.keys : ('fields' in op && Array.isArray(op.fields) ? op.fields : []);
        for (const k of keys) {
          delete result[k];
        }
        break;
      }
      case JsonMapOpKind.DEFAULT: {
        const k = 'key' in op && op.key ? op.key : ('field' in op && op.field ? op.field : '');
        if (k && (!(k in result) || result[k] === undefined || result[k] === null)) {
          result[k] = op.value;
        }
        break;
      }
      case JsonMapOpKind.COERCE: {
        const k = 'key' in op && op.key ? op.key : ('field' in op && op.field ? op.field : '');
        if (k && k in result) {
          result[k] = coerceValue(result[k], op.to);
        }
        break;
      }
    }
  }

  return result;
}
