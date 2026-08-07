export type RuleConditionOp = 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'in';

export interface RuleCondition {
  field: string;
  op: RuleConditionOp;
  value: unknown;
}

export type AsyncCheckFn = (ctx: Record<string, unknown>) => Promise<boolean>;

export interface Rule {
  id: string;
  name: string;
  category?: string;
  priority?: number;
  effect: 'allow' | 'deny';
  conditions: RuleCondition[];
  asyncCheck?: AsyncCheckFn;
}
