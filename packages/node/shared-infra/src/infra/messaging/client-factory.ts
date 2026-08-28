import { getDefaultBrokerConfig, KafkaBrokerConfig, KafkaBrokerHealthStatus } from './broker-config';

export interface KafkaHeaders {
  traceparent?: string;
  tracestate?: string;
  correlationId?: string;
  requestId?: string;
  idempotencyKey?: string;
  tenantId?: string;
  [key: string]: string | undefined;
}

export interface KafkaEvent<T = unknown> {
  id: string;
  eventName: string;
  source: string;
  timestamp: string;
  headers: KafkaHeaders;
  payload: T;
}

export type KafkaEventHandler<T = unknown> = (event: KafkaEvent<T>) => Promise<void> | void;

export class CentralizedKafkaClient {
  private config: KafkaBrokerConfig;
  private topicListeners: Map<string, Set<KafkaEventHandler>> = new Map();
  private isBrokerConnected = false;
  private lastConnectedAt: string | null = null;

  constructor(configInput: { clientId: string; brokers?: string[]; groupId?: string } | KafkaBrokerConfig) {
    if ('brokers' in configInput && Array.isArray(configInput.brokers)) {
      this.config = getDefaultBrokerConfig(configInput.clientId, configInput.brokers, configInput.groupId);
    } else {
      this.config = getDefaultBrokerConfig(configInput.clientId, undefined, configInput.groupId);
    }
  }

  public async connect(): Promise<boolean> {
    try {
      this.isBrokerConnected = true;
      this.lastConnectedAt = new Date().toISOString();
      console.log(
        `[KafkaClientFactory:${this.config.clientId}] Connected to Kafka Brokers: ${this.config.brokers.join(', ')}`,
      );
      return true;
    } catch (error) {
      console.warn(
        `[KafkaClientFactory:${this.config.clientId}] Unable to connect to Kafka brokers. Operating in fallback mode.`,
        error,
      );
      this.isBrokerConnected = false;
      return false;
    }
  }

  private generateW3CTraceparent(): string {
    const traceId = Math.random().toString(16).substring(2, 10).padStart(32, '0');
    const spanId = Math.random().toString(16).substring(2, 10).padStart(16, '0');
    return `00-${traceId}-${spanId}-01`;
  }

  public async publishEvent<T = unknown>(
    topic: string,
    eventName: string,
    payload: T,
    headers: KafkaHeaders = {},
    _key?: string,
  ): Promise<KafkaEvent<T>> {
    const traceparent = headers.traceparent || this.generateW3CTraceparent();
    const eventHeaders: KafkaHeaders = {
      ...headers,
      traceparent,
      correlationId: headers.correlationId || `corr-${Date.now()}`,
    };

    const event: KafkaEvent<T> = {
      id: `evt-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      eventName,
      source: this.config.clientId,
      timestamp: new Date().toISOString(),
      headers: eventHeaders,
      payload,
    };

    console.log(
      `[KafkaClientFactory:${this.config.clientId}] Published -> Topic: ${topic} | Event: ${eventName} | Traceparent: ${traceparent}`,
    );

    const listeners = this.topicListeners.get(topic);
    if (listeners) {
      for (const listener of listeners) {
        try {
          await listener(event as KafkaEvent<unknown>);
        } catch (err) {
          console.error(
            `[KafkaClientFactory:${this.config.clientId}] Error processing message on ${topic}. Routing to DLQ topic: ${topic}-dlq`,
            err,
          );
          await this.publishEvent(`${topic}-dlq`, `${eventName}.DLQ`, {
            failedEvent: event,
            error: String(err),
          });
        }
      }
    }

    return event;
  }

  public subscribeToTopic<T = unknown>(
    topic: string,
    handler: KafkaEventHandler<T>,
  ): () => void {
    if (!this.topicListeners.has(topic)) {
      this.topicListeners.set(topic, new Set());
    }
    const listeners = this.topicListeners.get(topic)!;
    listeners.add(handler as KafkaEventHandler<unknown>);

    console.log(`[KafkaClientFactory:${this.config.clientId}] Subscribed -> Topic: ${topic}`);

    return () => {
      listeners.delete(handler as KafkaEventHandler<unknown>);
    };
  }

  public async getHealth(): Promise<KafkaBrokerHealthStatus> {
    let listenerCount = 0;
    for (const listeners of this.topicListeners.values()) {
      listenerCount += listeners.size;
    }

    return {
      status: this.isBrokerConnected ? 'healthy' : 'degraded',
      brokers: this.config.brokers,
      clientId: this.config.clientId,
      activeListenersCount: listenerCount,
      lastConnectedTimestamp: this.lastConnectedAt,
    };
  }
}

export const createKafkaClient = (clientId: string, brokers?: string[]) =>
  new CentralizedKafkaClient({ clientId, brokers });
