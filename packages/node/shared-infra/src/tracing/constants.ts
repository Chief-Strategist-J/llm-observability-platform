export const TRACING_CONSTANTS = {
  ATTR_CQRS_EVENT_NAME: "cqrs.event_name",
  ATTR_CQRS_EVENT_ID: "cqrs.event_id",
  ATTR_CQRS_TOPIC: "cqrs.topic",
  ATTR_CQRS_TENANT_ID: "cqrs.tenant_id",
  ATTR_CQRS_USER_ID: "cqrs.user_id",
  ATTR_CQRS_ORG_ID: "cqrs.org_id",
  ATTR_HTTP_ROUTE: "http.route",
  ATTR_VALIDATION_STATUS: "validation.status",
  ATTR_VALIDATION_ERRORS: "validation.errors",

  STATUS_SUCCESS: "success",
  STATUS_VALIDATION_FAILED: "validation_failed",
  ERROR_INVALID_REQUEST: "Invalid request parameters",
} as const;
