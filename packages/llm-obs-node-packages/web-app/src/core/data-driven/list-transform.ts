import type { ListOp } from "./transform.types";
import { ListOpKind, FilterComparison, SortDirection } from "./transform.types";

export function transformList<T extends Record<string, unknown>>(items: T[], ops: ListOp[]): T[] {
  return ops.reduce<any[]>((acc, step) => {
    switch (step.op) {
      case ListOpKind.FILTER:
        return acc.filter((item) => {
          const val = item[step.field];
          const cmp = step.cmp ?? FilterComparison.EQ;
          if (cmp === FilterComparison.EQ) return val === step.value;
          if (cmp === FilterComparison.NEQ) return val !== step.value;
          if (cmp === FilterComparison.GT) return Number(val) > Number(step.value);
          if (cmp === FilterComparison.LT) return Number(val) < Number(step.value);
          if (cmp === FilterComparison.CONTAINS) return String(val ?? "").toLowerCase().includes(String(step.value).toLowerCase());
          return true;
        });
      case ListOpKind.SEARCH: {
        const q = step.query.toLowerCase().trim();
        if (!q) return acc;
        return acc.filter((item) =>
          step.fields.some((f) => String(item[f] ?? "").toLowerCase().includes(q))
        );
      }
      case ListOpKind.SORT: {
        const dir = step.dir === SortDirection.DESC ? -1 : 1;
        return [...acc].sort((a, b) => {
          const va = a[step.field];
          const vb = b[step.field];
          if (va === vb) return 0;
          return (va ?? "") > (vb ?? "") ? dir : -dir;
        });
      }
      case ListOpKind.PAGINATE: {
        const start = (step.page - 1) * step.pageSize;
        return acc.slice(start, start + step.pageSize);
      }
      case ListOpKind.PICK:
        return acc.map((item) =>
          step.fields.reduce((p, f) => (f in item ? { ...p, [f]: item[f] } : p), {})
        );
      case ListOpKind.GROUP_BY:
        return acc;
      default:
        return acc;
    }
  }, items);
}
