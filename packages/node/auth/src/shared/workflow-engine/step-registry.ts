export type StepHandler = (params: Record<string, unknown>, ctx: Record<string, unknown>) => Promise<unknown>;

const registry = new Map<string, StepHandler>();

export const stepRegistry = {
  register(type: string, handler: StepHandler) {
    registry.set(type, handler);
  },
  get(type: string): StepHandler | undefined {
    return registry.get(type);
  },
  has(type: string): boolean {
    return registry.has(type);
  },
};
