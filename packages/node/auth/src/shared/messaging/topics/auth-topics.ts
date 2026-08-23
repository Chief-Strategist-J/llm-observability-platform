export const AUTH_KAFKA_TOPICS = {
  AUTH_EVENTS: 'auth.events.v1',
  USER_EVENTS: 'auth.user-events.v1',
  AUDIT_EVENTS: 'auth.audit-events.v1',
  DLQ: {
    AUTH_EVENTS_DLQ: 'auth.events.v1-dlq',
    USER_EVENTS_DLQ: 'auth.user-events.v1-dlq',
  },
} as const;
