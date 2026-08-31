import type { Rule, RuleCondition } from './rule.types';
import { withSpan } from '../tracing/tracer';
import { RULES_ENGINE_CONSTANTS } from './constants';

export * from './constants';

function evaluateCondition(cond: RuleCondition, ctx: Record<string, unknown>): boolean {
  const actual = ctx[cond.field];
  switch (cond.op) {
    case RULES_ENGINE_CONSTANTS.OP_EQUALS:
      return actual === cond.value;
    case RULES_ENGINE_CONSTANTS.OP_NOT_EQUALS:
      return actual !== cond.value;
    case RULES_ENGINE_CONSTANTS.OP_GREATER_THAN:
      return typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof cond.value === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual > cond.value;
    case RULES_ENGINE_CONSTANTS.OP_LESS_THAN:
      return typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof cond.value === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual < cond.value;
    case RULES_ENGINE_CONSTANTS.OP_CONTAINS:
      return typeof actual === RULES_ENGINE_CONSTANTS.TYPE_STRING && typeof cond.value === RULES_ENGINE_CONSTANTS.TYPE_STRING && actual.includes(cond.value as string);
    case RULES_ENGINE_CONSTANTS.OP_IN:
      return Array.isArray(cond.value) && cond.value.includes(actual);
    default:
      return false;
  }
}

export async function resolveRules(
  rules: Rule[],
  ctx: Record<string, unknown>,
): Promise<Rule[]> {
  return withSpan(RULES_ENGINE_CONSTANTS.SPAN_RESOLVE_RULES, async (span) => {
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_EVALUATED_COUNT, rules.length);
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

    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_COUNT, activeRules.length);
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_IDS, JSON.stringify(activeRules.map((r) => r.id)));
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_NAMES, JSON.stringify(activeRules.map((r) => r.name)));

    return activeRules;
  });
}
