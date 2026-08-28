export interface FeatureModule {
  reducer: any;
  saga: () => Generator;
}

const registry = new Map<string, FeatureModule>();

export const featureRegistry = {
  register(name: string, mod: FeatureModule): void {
    registry.set(name, mod);
  },
  getAll(): [string, FeatureModule][] {
    return Array.from(registry.entries());
  },
  get(name: string): FeatureModule | undefined {
    return registry.get(name);
  },
};
