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
    const activeRules: Rule[] = [];

    for (const rule of sorted) {
      const conditionsMet = rule.conditions.every((cond) => conditionRegistry.evaluate(cond, ctx));
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
