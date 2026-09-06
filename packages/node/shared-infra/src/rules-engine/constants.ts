export const RULES_ENGINE_CONSTANTS = {
  OP_EQUALS: "equals",
  OP_NOT_EQUALS: "not_equals",
  OP_GREATER_THAN: "greater_than",
  OP_LESS_THAN: "less_than",
  OP_GTE: "gte",
  OP_LTE: "lte",
  OP_CONTAINS: "contains",
  OP_IN: "in",
  OP_REGEX: "regex",

  TYPE_NUMBER: "number",
  TYPE_STRING: "string",

  SPAN_RESOLVE_RULES: "RulesEngine.resolveRules",
  ATTR_EVALUATED_COUNT: "rules.evaluated_count",
  ATTR_TRIGGERED_COUNT: "rules.triggered_count",
  ATTR_TRIGGERED_IDS: "rules.triggered_ids",
  ATTR_TRIGGERED_NAMES: "rules.triggered_names",
  ATTR_CODE_FUNCTION: "code.function",
  ATTR_CODE_FILEPATH: "code.filepath",
  ATTR_CODE_LINENO: "code.lineno",

  // Decision Span Events
  EVENT_RULE_EVALUATED: "decision.rule_evaluated",
  EVENT_ASYNC_CHECK_EVALUATED: "decision.async_check_evaluated",

  // Error Codes
  ERR_VALIDATION_FAILED: "ERR_VALIDATION_FAILED",
  ERR_CIRCUIT_OPEN: "ERR_CIRCUIT_OPEN",
  ERR_HTTP_FAILED: "ERR_HTTP_FAILED",
  ERR_RULE_DENIED: "ERR_RULE_DENIED",
  ERR_UNKNOWN: "ERR_UNKNOWN",
  ERR_SSRF_PROTOCOL_BLOCKED: "ERR_SSRF_PROTOCOL_BLOCKED",
  ERR_SSRF_IP_BLOCKED: "ERR_SSRF_IP_BLOCKED",
  ERR_SSRF_ALLOWLIST_VIOLATION: "ERR_SSRF_ALLOWLIST_VIOLATION",
  ERR_SSRF_DNS_RESOLVED_BLOCKED: "ERR_SSRF_DNS_RESOLVED_BLOCKED",
  ERR_SSRF_INVALID_URL: "ERR_SSRF_INVALID_URL",
  ERR_CONTEXT_STORAGE_INIT_FAILED: "ERR_CONTEXT_STORAGE_INIT_FAILED",
  ERR_UNAUTHORIZED: "ERR_UNAUTHORIZED",
  ERR_FORBIDDEN: "ERR_FORBIDDEN",
  ERR_NOT_FOUND: "ERR_NOT_FOUND",
  ERR_SERVICE_UNREACHABLE: "ERR_SERVICE_UNREACHABLE",

  // Error Categories
  CAT_VALIDATION: "validation",
  CAT_NETWORK: "network",
  CAT_CIRCUIT_BREAKER: "circuit_breaker",
  CAT_RULE_BREACH: "rule_breach",
  CAT_INTERNAL: "internal",

  // Error Severities
  SEV_INFO: "info",
  SEV_WARNING: "warning",
  SEV_ERROR: "error",
  SEV_CRITICAL: "critical",

  // Error Messages
  MSG_UNKNOWN_ERROR: "An unknown platform error occurred",
  MSG_VALIDATION_FAILED: "Request payload failed Zod schema validation",
  MSG_CIRCUIT_OPEN: "Request blocked due to active circuit breaker OPEN state",
  MSG_HTTP_FAILED: "HTTP downstream service invocation failed",
  MSG_RULE_DENIED: "Action denied by business rules engine evaluation",
  MSG_SSRF_PROTOCOL_BLOCKED: "Blocked insecure destination URL protocol scheme",
  MSG_SSRF_IP_BLOCKED: "SSRF Blocked: Target host is a restricted private or loopback address",
  MSG_SSRF_ALLOWLIST_VIOLATION: "SSRF Violation: Target host is missing from permitted destination allowlist",
  MSG_SSRF_DNS_RESOLVED_BLOCKED: "SSRF Blocked: Resolved IP address for target host belongs to a restricted private subnet",
  MSG_SSRF_INVALID_URL: "Invalid destination URL string provided for security validation",
  MSG_CONTEXT_STORAGE_INIT_FAILED: "AsyncLocalStorage context storage initialization fallback to memory adapter",
  MSG_UNAUTHORIZED: "Invalid login credentials or unauthorized session. Please verify your credentials.",
  MSG_FORBIDDEN: "Access denied. You do not have permission to perform this operation.",
  MSG_NOT_FOUND: "Requested service resource or endpoint was not found.",
  MSG_SERVICE_UNREACHABLE: "Target service is unreachable or offline. Please check that the Docker service is running.",
} as const;
