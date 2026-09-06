import type { KafkaEvent, CentralizedKafkaClient } from '../../infra/messaging/client-factory';
import { MessagingTracer } from '../tracing/messaging-tracer';

export type ConsumerNextFn<T = unknown> = (
  event: KafkaEvent<T>,
  topic: string,
) => Promise<void>;

export type ConsumerMiddleware = <T = unknown>(
  event: KafkaEvent<T>,
  topic: string,
  next: ConsumerNextFn<T>,
) => Promise<void>;

export class ConsumerMiddlewarePipeline {
  private middlewares: ConsumerMiddleware[] = [];

  public use(middleware: ConsumerMiddleware): this {
    this.middlewares.push(middleware);
    return this;
  }

  public execute<T = unknown>(
    event: KafkaEvent<T>,
    topic: string,
    baseHandle: ConsumerNextFn<T>,
  ): Promise<void> {
    let index = -1;
    const dispatch = (i: number, ev: KafkaEvent<T>, top: string): Promise<void> => {
      if (i <= index) return Promise.reject(new Error('next() called multiple times in consumer middleware'));
      index = i;
      const fn = this.middlewares[i];
      if (!fn) return baseHandle(ev, top);
      return fn(ev, top, (nextEv, nextTop) => dispatch(i + 1, nextEv, nextTop));
    };
    return dispatch(0, event, topic);
  }
}

// --- Idempotency Store ---

export class IdempotencyStore {
  private static instance: IdempotencyStore;
  private processedIds = new Set<string>();

  public static getInstance(): IdempotencyStore {
    if (!IdempotencyStore.instance) {
      IdempotencyStore.instance = new IdempotencyStore();
    }
    return IdempotencyStore.instance;
  }

  public has(eventId: string): boolean {
    return this.processedIds.has(eventId);
  }

  public markProcessed(eventId: string): void {
    this.processedIds.add(eventId);
  }

  public clear(): void {
    this.processedIds.clear();
  }
}

// --- Standard Builtin Consumer Middlewares ---

export const idempotencyConsumerMiddleware: ConsumerMiddleware = async (
  event,
  topic,
  next,
) => {
  const store = IdempotencyStore.getInstance();
  const key = event.headers?.idempotencyKey || event.headers?.requestId || event.id;

  if (store.has(key)) {
    console.warn(
      `[IdempotencyMiddleware] Duplicate event ignored -> Key: ${key} | Topic: ${topic} | Event: ${event.eventName}`,
    );
    return;
  }
  await next(event, topic);
  store.markProcessed(key);
};

export const tracingConsumerMiddleware: ConsumerMiddleware = async (
  event,
  topic,
  next,
) => {
  const span = MessagingTracer.createConsumerSpan(event as KafkaEvent<unknown>, topic);
  try {
    await next(event, topic);
    MessagingTracer.finishSpan(span);
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    MessagingTracer.finishSpan(span, error);
    throw error;
  }
};

export const dlqConsumerMiddleware = (client: CentralizedKafkaClient): ConsumerMiddleware => {
  return async (event, topic, next) => {
    try {
      await next(event, topic);
    } catch (err) {
      console.error(
        `[DlqConsumerMiddleware] Failure processing ${event.eventName} on ${topic}. Routing to DLQ (${topic}-dlq)...`,
        err,
      );
      await client.publishEvent(
        `${topic}-dlq`,
        `${event.eventName}.DLQ`,
        {
          failedEvent: event,
          error: String(err),
        },
        event.headers,
      );
    }
  };
};

export const retryConsumerMiddleware = (
  maxRetries = 3,
  initialDelayMs = 50,
  jitterFactor = 0.5,
): ConsumerMiddleware => {
  return async (event, topic, next) => {
    let attempt = 0;
    while (attempt < maxRetries) {
      try {
        await next(event, topic);
        return;
      } catch (err) {
        attempt++;
        if (attempt >= maxRetries) {
          throw err;
        }
        const baseDelay = initialDelayMs * Math.pow(2, attempt - 1);
        const jitter = Math.random() * (baseDelay * jitterFactor);
        const totalDelay = Math.floor(baseDelay + jitter);

        console.warn(
          `[RetryConsumerMiddleware] Attempt ${attempt}/${maxRetries} failed for event ${event.id}. Retrying in ${totalDelay}ms...`,
        );
        await new Promise((resolve) => setTimeout(resolve, totalDelay));
      }
    }
  };
};

export const loggingConsumerMiddleware: ConsumerMiddleware = async (
  event,
  topic,
  next,
) => {
  console.log(`[ConsumerMiddleware] Incoming Event -> ${topic}:${event.eventName} [ID: ${event.id}]`);
  await next(event, topic);
};
