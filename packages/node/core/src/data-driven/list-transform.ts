import type { ListOp } from './transform.types';

export function transformList<T extends Record<string, unknown>>(
  rows: T[],
  ops: ListOp[],
): T[] {
  let result = [...rows];

  for (const op of ops) {
    switch (op.op) {
      case 'filter': {
        result = result.filter((row) => row[op.field] === op.value);
        break;
      }
      case 'search': {
        const q = op.query.toLowerCase();
        result = result.filter((row) =>
          op.fields.some((field) => {
            const val = row[field];
            return val !== undefined && val !== null && String(val).toLowerCase().includes(q);
          }),
        );
        break;
      }
      case 'sort': {
        const dir = op.direction === 'asc' ? 1 : -1;
        result.sort((a, b) => {
          const aVal = a[op.field];
          const bVal = b[op.field];
          if (aVal === bVal) return 0;
          if (aVal === undefined || aVal === null) return 1;
          if (bVal === undefined || bVal === null) return -1;
          return aVal < bVal ? -dir : dir;
        });
        break;
      }
      case 'paginate': {
        const start = (op.page - 1) * op.pageSize;
        result = result.slice(start, start + op.pageSize);
        break;
      }
      case 'pick': {
        result = result.map((row) => {
          const picked = {} as Record<string, unknown>;
          for (const field of op.fields) {
            if (field in row) {
              picked[field] = row[field];
            }
          }
          return picked as T;
        });
        break;
      }
      case 'groupBy': {
        break;
      }
    }
  }

  return result;
}
