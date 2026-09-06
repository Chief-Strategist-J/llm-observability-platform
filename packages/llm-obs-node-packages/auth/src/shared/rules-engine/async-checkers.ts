export type AsyncChecker = (ctx: Record<string, unknown>, params?: Record<string, unknown>) => Promise<boolean>;

const registry = new Map<string, AsyncChecker>();

export const asyncCheckerRegistry = {
  register(name: string, checker: AsyncChecker) {
    registry.set(name, checker);
  },
  get(name: string): AsyncChecker | undefined {
    return registry.get(name);
  },
  has(name: string): boolean {
    return registry.has(name);
  },
};
