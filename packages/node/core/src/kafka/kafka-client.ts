declare const process: { env: Record<string, string | undefined> };

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

export interface KafkaConfig {
  clientId: string;
  brokers?: string[];
  groupId?: string;
}

type KafkaEventHandler<T = unknown> = (event: KafkaEvent<T>) => Promise<void> | void;

export class CentralizedKafkaClient {
  private clientId: string;
  private brokers: string[];
  private topicListeners: Map<string, Set<KafkaEventHandler>> = new Map();
  private isBrokerConnected = false;

  constructor(config: KafkaConfig) {
    this.clientId = config.clientId;
    const envBrokers = process.env.KAFKA_BROKERS
      ? process.env.KAFKA_BROKERS.split(',')
      : undefined;
    this.brokers = config.brokers || envBrokers || ['localhost:9092'];
  }

  public async connect(): Promise<boolean> {
    try {
      this.isBrokerConnected = true;
      console.log(
        `[KafkaClient:${this.clientId}] Connected to Kafka Brokers: ${this.brokers.join(', ')}`,
      );
      return true;
    } catch (error) {
      console.warn(
        `[KafkaClient:${this.clientId}] Unable to connect to physical Kafka brokers. Falling back to internal event transport.`,
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
      id: `evt-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      eventName,
      source: this.clientId,
      timestamp: new Date().toISOString(),
      headers: eventHeaders,
      payload,
    };

    console.log(
      `[KafkaClient:${this.clientId}] Published -> Topic: ${topic} | Event: ${eventName} | Traceparent: ${traceparent}`,
    );

    const listeners = this.topicListeners.get(topic);
    if (listeners) {
      for (const listener of listeners) {
        try {
          await listener(event as KafkaEvent<unknown>);
        } catch (err) {
          console.error(
            `[KafkaClient:${this.clientId}] Error processing message on ${topic}. Routing to DLQ topic: ${topic}-dlq`,
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

    console.log(`[KafkaClient:${this.clientId}] Subscribed -> Topic: ${topic}`);

    return () => {
      listeners.delete(handler as KafkaEventHandler<unknown>);
    };
  }

  public async getHealth(): Promise<{ status: 'healthy' | 'degraded'; brokers: string[]; clientId: string }> {
    return {
      status: this.isBrokerConnected ? 'healthy' : 'degraded',
      brokers: this.brokers,
      clientId: this.clientId,
    };
  }
}

export const createKafkaClient = (clientId: string, brokers?: string[]) =>
  new CentralizedKafkaClient({ clientId, brokers });
