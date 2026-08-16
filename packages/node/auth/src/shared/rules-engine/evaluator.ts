import { asyncCheckerRegistry } from './async-checkers';

export interface RuleCondition {
  field?: string;
  op?: 'eq' | 'ne' | 'gt' | 'lt' | 'in' | 'contains';
  value?: unknown;
  asyncChecker?: string;
  checkerParams?: Record<string, unknown>;
}

export interface Rule {
  id: string;
  name: string;
  priority: number;
  category: 'allow' | 'deny' | 'effect';
  conditions: RuleCondition[];
  effect?: string;
}

export async function evaluateRule(rule: Rule, ctx: Record<string, unknown>): Promise<boolean> {
  for (const cond of rule.conditions) {
    if (cond.asyncChecker) {
      const checker = asyncCheckerRegistry.get(cond.asyncChecker);
      if (!checker) return false;
      const passed = await checker(ctx, cond.checkerParams);
      if (!passed) return false;
      continue;
    }

    if (!cond.field || !cond.op) continue;
    const actual = ctx[cond.field];

    switch (cond.op) {
      case 'eq':
        if (actual !== cond.value) return false;
        break;
      case 'ne':
        if (actual === cond.value) return false;
        break;
      case 'gt':
        if (Number(actual) <= Number(cond.value)) return false;
        break;
      case 'lt':
        if (Number(actual) >= Number(cond.value)) return false;
        break;
      case 'in':
        if (!Array.isArray(cond.value) || !cond.value.includes(actual)) return false;
        break;
      case 'contains':
        if (!String(actual).includes(String(cond.value))) return false;
        break;
    }
  }

  return true;
}

export async function resolveRules(rules: Rule[], ctx: Record<string, unknown>): Promise<Rule[]> {
  const sorted = [...rules].sort((a, b) => b.priority - a.priority);
  const matched: Rule[] = [];

  for (const rule of sorted) {
    if (await evaluateRule(rule, ctx)) {
      matched.push(rule);
      if (rule.category === 'deny') {
        // Deny override stops further evaluation
        break;
      }
    }
  }

  return matched;
}
