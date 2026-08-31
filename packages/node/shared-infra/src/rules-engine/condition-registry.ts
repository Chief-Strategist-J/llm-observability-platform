import type { RuleCondition } from './rule.types';
import { RULES_ENGINE_CONSTANTS } from './constants';

export type ConditionHandlerFn = (actual: unknown, expected: unknown) => boolean;

class ConditionHandlerRegistry {
  private readonly handlers = new Map<string, ConditionHandlerFn>();

  constructor() {
    this.registerDefaults();
  }

  public register(op: string, handler: ConditionHandlerFn): void {
    this.handlers.set(op, handler);
  }

  public evaluate(cond: RuleCondition, ctx: Record<string, unknown>): boolean {
    const actual = ctx[cond.field];
    const handler = this.handlers.get(cond.op);
    return handler ? handler(actual, cond.value) : false;
  }

  private registerDefaults(): void {
    this.register(RULES_ENGINE_CONSTANTS.OP_EQUALS, (actual, expected) => actual === expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_NOT_EQUALS, (actual, expected) => actual !== expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_GREATER_THAN, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual > expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_LESS_THAN, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual < expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_GTE, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual >= expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_LTE, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_NUMBER && actual <= expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_CONTAINS, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_STRING && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_STRING && actual.includes(expected as string));
    this.register(RULES_ENGINE_CONSTANTS.OP_IN, (actual, expected) => Array.isArray(expected) && expected.includes(actual));
    this.register(RULES_ENGINE_CONSTANTS.OP_REGEX, (actual, expected) => typeof actual === RULES_ENGINE_CONSTANTS.TYPE_STRING && typeof expected === RULES_ENGINE_CONSTANTS.TYPE_STRING && new RegExp(expected as string).test(actual as string));
  }
}

export const conditionRegistry = new ConditionHandlerRegistry();
