import type { Rule } from './rule.types';
import { withSpan } from '../tracing/tracer';
import { getCallerInfo } from '../tracing/caller-info';
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
  const caller = getCallerInfo(2);
  return withSpan(RULES_ENGINE_CONSTANTS.SPAN_RESOLVE_RULES, async (span) => {
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_CODE_FUNCTION, caller.functionName);
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_CODE_FILEPATH, caller.filePath);
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_CODE_LINENO, caller.lineNumber);

    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_EVALUATED_COUNT, rules.length);
    const sorted = [...rules].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

    const activeRules: Rule[] = [];
    for (const rule of sorted) {
      const conditionsMet = rule.conditions.every((cond) => conditionRegistry.evaluate(cond, ctx));

      span.addEvent(RULES_ENGINE_CONSTANTS.EVENT_RULE_EVALUATED, {
        "rule.id": rule.id,
        "rule.name": rule.name,
        "rule.conditions_passed": conditionsMet,
        "rule.priority": rule.priority ?? 0,
      });

      if (!conditionsMet) {
        continue;
      }

      let asyncPassed = true;
      if (rule.asyncCheck) {
        asyncPassed = await rule.asyncCheck(ctx);
        span.addEvent(RULES_ENGINE_CONSTANTS.EVENT_ASYNC_CHECK_EVALUATED, {
          "rule.id": rule.id,
          "rule.async_passed": asyncPassed,
        });
      }

      if (asyncPassed) {
        activeRules.push(rule);
      }
    }

    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_COUNT, activeRules.length);
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_IDS, JSON.stringify(activeRules.map((r) => r.id)));
    span.setAttribute(RULES_ENGINE_CONSTANTS.ATTR_TRIGGERED_NAMES, JSON.stringify(activeRules.map((r) => r.name)));

    return activeRules;
  });
}
