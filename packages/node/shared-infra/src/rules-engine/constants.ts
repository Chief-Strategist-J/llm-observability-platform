export const RULES_ENGINE_CONSTANTS = {
  OP_EQUALS: "equals",
  OP_NOT_EQUALS: "not_equals",
  OP_GREATER_THAN: "greater_than",
  OP_LESS_THAN: "less_than",
  OP_CONTAINS: "contains",
  OP_IN: "in",

  TYPE_NUMBER: "number",
  TYPE_STRING: "string",

  SPAN_RESOLVE_RULES: "RulesEngine.resolveRules",
  ATTR_EVALUATED_COUNT: "rules.evaluated_count",
  ATTR_TRIGGERED_COUNT: "rules.triggered_count",
  ATTR_TRIGGERED_IDS: "rules.triggered_ids",
  ATTR_TRIGGERED_NAMES: "rules.triggered_names",
} as const;
