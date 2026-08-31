import type { Rule } from './rule.types';

class CentralizedRuleRegistry {
  private readonly rulesMap = new Map<string, Rule>();

  public register(rule: Rule): void {
    this.rulesMap.set(rule.id, rule);
  }

  public registerSet(rules: Rule[]): void {
    rules.forEach((r) => this.register(r));
  }

  public get(id: string): Rule | undefined {
    return this.rulesMap.get(id);
  }

  public getAll(): Rule[] {
    return Array.from(this.rulesMap.values());
  }

  public getByCategory(category: string): Rule[] {
    return this.getAll().filter((r) => r.category === category);
  }

  public clear(): void {
    this.rulesMap.clear();
  }
}

export const ruleRegistry = new CentralizedRuleRegistry();
