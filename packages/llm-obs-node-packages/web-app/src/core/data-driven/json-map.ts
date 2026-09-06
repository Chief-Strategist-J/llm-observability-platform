import type { JsonMapOp } from "./transform.types";
import { JsonMapOpKind, CoerceTarget } from "./transform.types";

export function mapJson(obj: Record<string, unknown>, ops: JsonMapOp[]): Record<string, unknown> {
  return ops.reduce((acc, step) => {
    switch (step.op) {
      case JsonMapOpKind.RENAME: {
        const { [step.from]: val, ...rest } = acc;
        return step.from in acc ? { ...rest, [step.to]: val } : acc;
      }
      case JsonMapOpKind.PICK:
        return step.keys.reduce((p, k) => (k in acc ? { ...p, [k]: acc[k] } : p), {});
      case JsonMapOpKind.OMIT:
        return Object.fromEntries(Object.entries(acc).filter(([k]) => !step.keys.includes(k)));
      case JsonMapOpKind.DEFAULT:
        return acc[step.key] === undefined || acc[step.key] === null ? { ...acc, [step.key]: step.value } : acc;
      case JsonMapOpKind.COERCE: {
        const raw = acc[step.key];
        if (raw === undefined || raw === null) return acc;
        let v: unknown = raw;
        if (step.to === CoerceTarget.STRING) v = String(raw);
        if (step.to === CoerceTarget.NUMBER) v = Number(raw);
        if (step.to === CoerceTarget.BOOLEAN) v = Boolean(raw);
        if (step.to === CoerceTarget.DATE) v = new Date(String(raw));
        return { ...acc, [step.key]: v };
      }
      default:
        return acc;
    }
  }, { ...obj });
}
