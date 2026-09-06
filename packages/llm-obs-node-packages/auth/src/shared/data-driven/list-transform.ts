export type ListOp =
  | { op: 'filter'; field: string; eq?: unknown; ne?: unknown; in?: unknown[] }
  | { op: 'search'; fields: string[]; query: string }
  | { op: 'sort'; field: string; dir?: 'asc' | 'desc' }
  | { op: 'paginate'; page: number; limit: number };

export function transformList<T extends Record<string, unknown>>(
  list: T[],
  ops: ListOp[]
): T[] {
  let result = [...list];

  for (const op of ops) {
    switch (op.op) {
      case 'filter': {
        result = result.filter((item) => {
          const val = item[op.field];
          if (op.eq !== undefined && val !== op.eq) return false;
          if (op.ne !== undefined && val === op.ne) return false;
          if (op.in !== undefined && !op.in.includes(val)) return false;
          return true;
        });
        break;
      }
      case 'search': {
        const q = op.query.toLowerCase().trim();
        if (q) {
          result = result.filter((item) =>
            op.fields.some((f) => String(item[f] ?? '').toLowerCase().includes(q))
          );
        }
        break;
      }
      case 'sort': {
        const dir = op.dir === 'desc' ? -1 : 1;
        result.sort((a, b) => {
          const va = a[op.field] as any;
          const vb = b[op.field] as any;
          if (va < vb) return -1 * dir;
          if (va > vb) return 1 * dir;
          return 0;
        });
        break;
      }
      case 'paginate': {
        const start = (op.page - 1) * op.limit;
        result = result.slice(start, start + op.limit);
        break;
      }
    }
  }

  return result;
}
