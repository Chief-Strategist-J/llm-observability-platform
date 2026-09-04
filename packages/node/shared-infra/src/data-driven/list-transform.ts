import type { ListOp } from './transform.types';
import { ListOpKind, SortDirection } from './transform.types';

export function transformList<T extends Record<string, unknown>>(
  rows: T[],
  ops: ListOp[],
): T[] {
  let result = [...rows];

  for (const op of ops) {
    switch (op.op) {
      case ListOpKind.FILTER: {
        result = result.filter((row) => row[op.field] === op.value);
        break;
      }
      case ListOpKind.SEARCH: {
        const q = op.query.toLowerCase();
        result = result.filter((row) =>
          op.fields.some((field) => {
            const val = row[field];
            return val !== undefined && val !== null && String(val).toLowerCase().includes(q);
          }),
        );
        break;
      }
      case ListOpKind.SORT: {
        const sortDir = 'dir' in op && op.dir ? op.dir : ('direction' in op && op.direction ? op.direction : SortDirection.ASC);
        const dir = sortDir === SortDirection.ASC ? 1 : -1;
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
      case ListOpKind.PAGINATE: {
        const start = (op.page - 1) * op.pageSize;
        result = result.slice(start, start + op.pageSize);
        break;
      }
      case ListOpKind.PICK: {
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
      case ListOpKind.GROUP_BY: {
        break;
      }
    }
  }

  return result;
}
