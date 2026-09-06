declare const process: { env: Record<string, string | undefined> };

export interface KafkaBrokerConfig {
  clientId: string;
  brokers: string[];
  groupId?: string;
  connectionTimeoutMs?: number;
  requestTimeoutMs?: number;
  maxInFlightRequests?: number;
  enableIdempotence?: boolean;
  retryOptions?: {
    maxRetries: number;
    initialRetryTimeMs: number;
  };
}

export function getDefaultBrokerConfig(clientId: string, overrideBrokers?: string[], groupId?: string): KafkaBrokerConfig {
  const envBrokers = process.env.KAFKA_BROKERS
    ? process.env.KAFKA_BROKERS.split(',').map((b) => b.trim()).filter(Boolean)
    : undefined;

  return {
    clientId,
    brokers: overrideBrokers || envBrokers || ['localhost:9092'],
    groupId: groupId || `${clientId}-group`,
    connectionTimeoutMs: 5000,
    requestTimeoutMs: 30000,
    maxInFlightRequests: 5,
    enableIdempotence: true,
    retryOptions: {
      maxRetries: 5,
      initialRetryTimeMs: 100,
    },
  };
}

export interface KafkaBrokerHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  brokers: string[];
  clientId: string;
  activeListenersCount: number;
  lastConnectedTimestamp: string | null;
}
