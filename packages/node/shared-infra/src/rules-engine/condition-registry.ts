import type { RuleCondition } from './rule.types';
import { RULES_ENGINE_CONSTANTS } from './constants';

export type ConditionHandlerFn = (actual: unknown, expected: unknown) => boolean;

function isNumber(val: unknown): val is number {
  return typeof val === RULES_ENGINE_CONSTANTS.TYPE_NUMBER;
}

function isString(val: unknown): val is string {
  return typeof val === RULES_ENGINE_CONSTANTS.TYPE_STRING;
}

export function getSafeContextValue(ctx: Record<string, unknown>, fieldPath: string): unknown {
  if (!ctx || typeof ctx !== 'object' || !fieldPath) {
    return undefined;
  }

  if (fieldPath.includes('__proto__') || fieldPath.includes('constructor') || fieldPath.includes('prototype')) {
    return undefined;
  }

  const parts = fieldPath.split('.');
  let current: any = ctx;
  for (const part of parts) {
    if (current === null || current === undefined || typeof current !== 'object') {
      return undefined;
    }
    if (part === '__proto__' || part === 'constructor' || part === 'prototype') {
      return undefined;
    }
    current = current[part];
  }
  return current;
}

class ConditionHandlerRegistry {
  private readonly handlers = new Map<string, ConditionHandlerFn>();

  constructor() {
    this.registerDefaults();
  }

  public register(op: string, handler: ConditionHandlerFn): void {
    this.handlers.set(op, handler);
  }

  public evaluate(cond: RuleCondition, ctx: Record<string, unknown>): boolean {
    const actual = getSafeContextValue(ctx, cond.field);
    const handler = this.handlers.get(cond.op);
    return handler ? handler(actual, cond.value) : false;
  }

  private registerDefaults(): void {
    this.register(RULES_ENGINE_CONSTANTS.OP_EQUALS, (actual, expected) => actual === expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_NOT_EQUALS, (actual, expected) => actual !== expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_GREATER_THAN, (actual, expected) => isNumber(actual) && isNumber(expected) && actual > expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_LESS_THAN, (actual, expected) => isNumber(actual) && isNumber(expected) && actual < expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_GTE, (actual, expected) => isNumber(actual) && isNumber(expected) && actual >= expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_LTE, (actual, expected) => isNumber(actual) && isNumber(expected) && actual <= expected);
    this.register(RULES_ENGINE_CONSTANTS.OP_CONTAINS, (actual, expected) => isString(actual) && isString(expected) && actual.includes(expected));
    this.register(RULES_ENGINE_CONSTANTS.OP_IN, (actual, expected) => Array.isArray(expected) && expected.includes(actual));
    this.register(RULES_ENGINE_CONSTANTS.OP_REGEX, (actual, expected) => isString(actual) && isString(expected) && new RegExp(expected).test(actual));
  }
}

export const conditionRegistry = new ConditionHandlerRegistry();
