import type { Rule, RuleCondition } from './rule.types';
import { withSpan } from '../tracing/tracer';

function evaluateCondition(cond: RuleCondition, ctx: Record<string, unknown>): boolean {
  const actual = ctx[cond.field];
  switch (cond.op) {
    case 'equals':
      return actual === cond.value;
    case 'not_equals':
      return actual !== cond.value;
    case 'greater_than':
      return typeof actual === 'number' && typeof cond.value === 'number' && actual > cond.value;
    case 'less_than':
      return typeof actual === 'number' && typeof cond.value === 'number' && actual < cond.value;
    case 'contains':
      return typeof actual === 'string' && typeof cond.value === 'string' && actual.includes(cond.value);
    case 'in':
      return Array.isArray(cond.value) && cond.value.includes(actual);
    default:
      return false;
  }
}

export async function resolveRules(
  rules: Rule[],
  ctx: Record<string, unknown>,
): Promise<Rule[]> {
  return withSpan("RulesEngine.resolveRules", async (span) => {
    span.setAttribute('rules.evaluated_count', rules.length);
    const sorted = [...rules].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));
    const activeRules: Rule[] = [];

    for (const rule of sorted) {
      const conditionsMet = rule.conditions.every((cond) => evaluateCondition(cond, ctx));
      if (!conditionsMet) continue;

      if (rule.asyncCheck) {
        const asyncPassed = await rule.asyncCheck(ctx);
        if (!asyncPassed) continue;
      }

      activeRules.push(rule);
    }

    span.setAttribute('rules.triggered_count', activeRules.length);
    span.setAttribute('rules.triggered_ids', JSON.stringify(activeRules.map((r) => r.id)));
    span.setAttribute('rules.triggered_names', JSON.stringify(activeRules.map((r) => r.name)));

    return activeRules;
  });
}
