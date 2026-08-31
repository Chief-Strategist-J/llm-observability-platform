import type { Rule } from './rule.types';
import { withSpan } from '../tracing/tracer';
import { RULES_ENGINE_CONSTANTS } from './constants';
import { conditionRegistry } from './condition-registry';

export * from './constants';
export * from './condition-registry';
export * from './rule-registry';
export * from './error-registry';

export async function resolveRules(
  rules: Rule[],
  ctx: Record<string, unknown>,
): Promise<Rule[]> {
  return withSpan(RULES_ENGINE_CONSTANTS.SPAN_RESOLVE_RULES, async (span) => {
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_EVALUATED_COUNT, rules.length);
    const sorted = [...rules].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

    const activeRules = await sorted.reduce(async (accPromise, rule) => {
      const acc = await accPromise;
      const conditionsMet = rule.conditions.every((cond) => conditionRegistry.evaluate(cond, ctx));
      const asyncPassed = conditionsMet && rule.asyncCheck ? await rule.asyncCheck(ctx) : conditionsMet;

      return asyncPassed ? [...acc, rule] : acc;
    }, Promise.resolve([] as Rule[]));

    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_COUNT, activeRules.length);
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_IDS, JSON.stringify(activeRules.map((r) => r.id)));
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_NAMES, JSON.stringify(activeRules.map((r) => r.name)));

    return activeRules;
  });
}
