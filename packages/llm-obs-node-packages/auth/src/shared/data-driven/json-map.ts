export type JsonMapOp =
  | { op: 'rename'; from: string; to: string }
  | { op: 'pick'; keys: string[] }
  | { op: 'omit'; keys: string[] }
  | { op: 'default'; key: string; value: unknown }
  | { op: 'coerce'; key: string; to: 'string' | 'number' | 'boolean' | 'date' };

export function mapJson<T extends Record<string, unknown>>(
  input: Record<string, unknown>,
  ops: JsonMapOp[]
): T {
  let result: Record<string, unknown> = { ...input };

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
        const next: Record<string, unknown> = {};
        for (const k of op.keys) {
          if (k in result) next[k] = result[k];
        }
        result = next;
        break;
      }
      case 'omit': {
        for (const k of op.keys) {
          delete result[k];
        }
        break;
      }
      case 'default': {
        if (result[op.key] === undefined || result[op.key] === null) {
          result[op.key] = op.value;
        }
        break;
      }
      case 'coerce': {
        const val = result[op.key];
        if (val !== undefined && val !== null) {
          if (op.to === 'string') result[op.key] = String(val);
          else if (op.to === 'number') result[op.key] = Number(val);
          else if (op.to === 'boolean') result[op.key] = Boolean(val);
          else if (op.to === 'date') result[op.key] = new Date(val as string | number);
        }
        break;
      }
    }
  }

  return result as T;
}
