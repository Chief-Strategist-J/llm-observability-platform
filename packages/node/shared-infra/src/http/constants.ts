export const HTTP_CONSTANTS = {
  DEFAULT_SERVICE_SUB: "web-app-service",
  DEFAULT_JWT_SECRET: "development-jwt-secret-key-32-bytes-min!!",
  JWT_ALG: "HS256",
  JWT_TYP: "JWT",
  HEADER_CONTENT_TYPE: "Content-Type",
  HEADER_AUTHORIZATION: "Authorization",
  HEADER_TRACEPARENT: "traceparent",
  HEADER_X_TRACE_ID: "x-trace-id",
  HEADER_X_REQUEST_ID: "x-request-id",
  HEADER_X_CORRELATION_ID: "x-correlation-id",
  HEADER_X_IDEMPOTENCY_KEY: "x-idempotency-key",
  HEADER_X_TENANT_ID: "x-tenant-id",
  HEADER_TRACESTATE: "tracestate",
  HEADER_RETRY_AFTER: "Retry-After",
  HEADER_CACHE_CONTROL: "Cache-Control",
  CONTENT_TYPE_JSON: "application/json",
  BEARER_PREFIX: "Bearer ",
  DEFAULT_TENANT_ID: "tenant-default",
  DEFAULT_TRACESTATE: "rojo=1",

  TRACER_NAME: "http-client",
  ERROR_NAME_ABORT: "AbortError",
  MSG_PIPELINE_FAILED: "HTTP Request Pipeline Failed",

  // Cache Directives
  CACHE_NO_CACHE: "no-cache",
  CACHE_NO_STORE: "no-store",

  // HTTP Methods
  METHOD_GET: "GET",
  METHOD_POST: "POST",
  METHOD_PATCH: "PATCH",
  METHOD_PUT: "PUT",
  METHOD_DELETE: "DELETE",

  // Circuit Breaker States
  CIRCUIT_CLOSED: "CLOSED",
  CIRCUIT_OPEN: "OPEN",
  CIRCUIT_HALF_OPEN: "HALF_OPEN",

  // OTEL Span Attributes & Code Telemetry
  ATTR_HTTP_METHOD: "http.method",
  ATTR_HTTP_URL: "http.url",
  ATTR_HTTP_STATUS_CODE: "http.status_code",
  ATTR_HTTP_CACHE_HIT: "http.cache_hit",
  ATTR_HTTP_CIRCUIT_STATE: "http.circuit_state",
  ATTR_HTTP_RETRY_ATTEMPT: "http.retry_attempt",
  ATTR_HTTP_RETRY_BACKOFF_MS: "http.retry_backoff_ms",
  ATTR_TENANT_ID: "tenant.id",
  ATTR_IDEMPOTENCY_KEY: "http.idempotency_key",
  ATTR_REQUEST_CANCELLED: "http.request_cancelled",
  ATTR_EXECUTION_PATH: "execution.path",
  ATTR_RESULT_STATUS: "execution.status",
  ATTR_ERROR_DETAIL: "execution.error_detail",
  ATTR_CODE_FUNCTION: "code.function",
  ATTR_CODE_FILEPATH: "code.filepath",
  ATTR_CODE_LINENO: "code.lineno",

  // Execution Paths
  PATH_POSITIVE: "positive_path",
  PATH_NEGATIVE: "negative_path",
  STATUS_SUCCESS: "success",
  STATUS_FAILURE: "failure",

  // Decision & Step Span Events
  EVENT_SINGLEFLIGHT_HIT: "decision.singleflight_collapsed",
  EVENT_CACHE_EVALUATED: "decision.cache_evaluated",
  EVENT_CIRCUIT_EVALUATED: "decision.circuit_breaker_evaluated",
  EVENT_REQUEST_CANCELLED: "decision.request_cancelled",
  EVENT_RETRY_DECISION: "decision.retry_evaluated",
  EVENT_EXECUTION_SUCCESS: "execution.success",
  EVENT_EXECUTION_FAILURE: "execution.failure",

  // Granular Pipeline Step Span Events
  EVENT_STEP_REQUEST_INTERCEPTORS: "step.request_interceptors_executed",
  EVENT_STEP_SINGLEFLIGHT_CHECK: "step.singleflight_check_completed",
  EVENT_STEP_HEADERS_RESOLVED: "step.header_providers_resolved",
  EVENT_STEP_FETCH_INITIATED: "step.fetch_attempt_initiated",
  EVENT_STEP_RESPONSE_INTERCEPTORS: "step.response_interceptors_executed",
  EVENT_STEP_ERROR_HANDLED: "step.error_interceptors_handled",

  // Attribute Keys for Decision Events
  KEY_CACHE_BYPASSED: "cache.bypassed",
  KEY_CACHE_HIT: "cache.hit",
  KEY_CACHE_KEY: "cache.key",
  KEY_CIRCUIT_STATE: "circuit.state",
  KEY_CIRCUIT_CAN_EXECUTE: "circuit.can_execute",
  KEY_CIRCUIT_FAILURES: "circuit.failures",
  KEY_CANCELLED_KEY: "request.cancelled_key",
  KEY_RETRY_ATTEMPT: "retry.attempt",
  KEY_RETRY_SHOULD_RETRY: "retry.should_retry",
  KEY_RETRY_ERROR_MSG: "retry.error_message",
  KEY_INTERCEPTORS_COUNT: "interceptors.count",
  KEY_HEADERS_COUNT: "headers.provider_count",
} as const;
