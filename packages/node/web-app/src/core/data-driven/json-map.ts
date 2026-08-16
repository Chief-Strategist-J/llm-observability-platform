import type { JsonMapOp } from "./transform.types";

export function mapJson(obj: Record<string, unknown>, ops: JsonMapOp[]): Record<string, unknown> {
  return ops.reduce((acc, step) => {
    switch (step.op) {
      case "rename": {
        const { [step.from]: val, ...rest } = acc;
        return step.from in acc ? { ...rest, [step.to]: val } : acc;
      }
      case "pick":
        return step.keys.reduce((p, k) => (k in acc ? { ...p, [k]: acc[k] } : p), {});
      case "omit":
        return Object.fromEntries(Object.entries(acc).filter(([k]) => !step.keys.includes(k)));
      case "default":
        return acc[step.key] === undefined || acc[step.key] === null ? { ...acc, [step.key]: step.value } : acc;
      case "coerce": {
        const raw = acc[step.key];
        if (raw === undefined || raw === null) return acc;
        let v: unknown = raw;
        if (step.to === "string") v = String(raw);
        if (step.to === "number") v = Number(raw);
        if (step.to === "boolean") v = Boolean(raw);
        if (step.to === "date") v = new Date(String(raw));
        return { ...acc, [step.key]: v };
      }
    }
  }, { ...obj });
}
