import type { ListOp } from "./transform.types";

export function transformList<T extends Record<string, unknown>>(items: T[], ops: ListOp[]): T[] {
  return ops.reduce<any[]>((acc, step) => {
    switch (step.op) {
      case "filter":
        return acc.filter((item) => {
          const val = item[step.field];
          const cmp = step.cmp ?? "eq";
          if (cmp === "eq") return val === step.value;
          if (cmp === "neq") return val !== step.value;
          if (cmp === "gt") return Number(val) > Number(step.value);
          if (cmp === "lt") return Number(val) < Number(step.value);
          if (cmp === "contains") return String(val ?? "").toLowerCase().includes(String(step.value).toLowerCase());
          return true;
        });
      case "search": {
        const q = step.query.toLowerCase().trim();
        if (!q) return acc;
        return acc.filter((item) =>
          step.fields.some((f) => String(item[f] ?? "").toLowerCase().includes(q))
        );
      }
      case "sort": {
        const dir = step.dir === "desc" ? -1 : 1;
        return [...acc].sort((a, b) => {
          const va = a[step.field];
          const vb = b[step.field];
          if (va === vb) return 0;
          return (va ?? "") > (vb ?? "") ? dir : -dir;
        });
      }
      case "paginate": {
        const start = (step.page - 1) * step.pageSize;
        return acc.slice(start, start + step.pageSize);
      }
      case "pick":
        return acc.map((item) =>
          step.fields.reduce((p, f) => (f in item ? { ...p, [f]: item[f] } : p), {})
        );
      case "groupBy":
        return acc;
    }
  }, items);
}
