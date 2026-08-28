export interface TopicMetadata {
  name: string;
  category: 'auth' | 'observability' | 'telemetry' | 'system';
  schemaVersion: string;
  partitions: number;
  description: string;
}

export const TOPIC_CATALOG: Record<string, TopicMetadata> = {
  USER_CREATED: {
    name: 'users.created.v1',
    category: 'auth',
    schemaVersion: 'v1',
    partitions: 3,
    description: 'Emitted when a new user completes registration',
  },
  USER_SIGNED_IN: {
    name: 'users.signed_in.v1',
    category: 'auth',
    schemaVersion: 'v1',
    partitions: 3,
    description: 'Emitted when a user signs in successfully',
  },
  TELEMETRY_LOGS_INGESTED: {
    name: 'telemetry.logs.ingested.v1',
    category: 'telemetry',
    schemaVersion: 'v1',
    partitions: 6,
    description: 'Emitted when raw telemetry log batch is ingested',
  },
  TELEMETRY_SPANS_INGESTED: {
    name: 'telemetry.spans.ingested.v1',
    category: 'telemetry',
    schemaVersion: 'v1',
    partitions: 6,
    description: 'Emitted when trace spans are ingested',
  },
  ALERT_TRIGGERED: {
    name: 'system.alerts.triggered.v1',
    category: 'system',
    schemaVersion: 'v1',
    partitions: 3,
    description: 'Emitted when system threshold alert triggers',
  },
};

export function getTopicMetadata(topicName: string): TopicMetadata | undefined {
  return Object.values(TOPIC_CATALOG).find((t) => t.name === topicName);
}
