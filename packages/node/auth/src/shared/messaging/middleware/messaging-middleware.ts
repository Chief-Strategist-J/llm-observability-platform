import { KafkaEvent, KafkaHeaders, CentralizedKafkaClient } from '@observability/core';
import { MessagingTracer } from '../tracing/messaging-tracer';

export type ProducerNextFn<T = unknown> = (
  topic: string,
  eventName: string,
  payload: T,
  headers?: KafkaHeaders,
) => Promise<KafkaEvent<T>>;

export type ProducerMiddleware = <T = unknown>(
  topic: string,
  eventName: string,
  payload: T,
  headers: KafkaHeaders | undefined,
  next: ProducerNextFn<T>,
) => Promise<KafkaEvent<T>>;

export type ConsumerNextFn<T = unknown> = (
  event: KafkaEvent<T>,
  topic: string,
) => Promise<void>;

export type ConsumerMiddleware = <T = unknown>(
  event: KafkaEvent<T>,
  topic: string,
  next: ConsumerNextFn<T>,
) => Promise<void>;

export class ProducerMiddlewarePipeline {
  private middlewares: ProducerMiddleware[] = [];

  public use(middleware: ProducerMiddleware): this {
    this.middlewares.push(middleware);
    return this;
  }

  public execute<T = unknown>(
    topic: string,
    eventName: string,
    payload: T,
    headers: KafkaHeaders | undefined,
    basePublish: ProducerNextFn<T>,
  ): Promise<KafkaEvent<T>> {
    let index = -1;
    const dispatch = (i: number, t: string, e: string, p: T, h?: KafkaHeaders): Promise<KafkaEvent<T>> => {
      if (i <= index) return Promise.reject(new Error('next() called multiple times'));
      index = i;
      const fn = this.middlewares[i];
      if (!fn) return basePublish(t, e, p, h);
      return fn(t, e, p, h, (nextTopic, nextEvent, nextPayload, nextHeaders) =>
        dispatch(i + 1, nextTopic, nextEvent, nextPayload, nextHeaders),
      );
    };
    return dispatch(0, topic, eventName, payload, headers);
  }
}

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
      if (i <= index) return Promise.reject(new Error('next() called multiple times'));
      index = i;
      const fn = this.middlewares[i];
      if (!fn) return baseHandle(ev, top);
      return fn(ev, top, (nextEv, nextTop) => dispatch(i + 1, nextEv, nextTop));
    };
    return dispatch(0, event, topic);
  }
}

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
          `[RetryMiddleware] Attempt ${attempt}/${maxRetries} failed for event ${event.id}. Retrying in ${totalDelay}ms (base: ${baseDelay}ms, jitter: +${Math.floor(jitter)}ms)...`,
        );
        await new Promise((resolve) => setTimeout(resolve, totalDelay));
      }
    }
  };
};

export const tracingProducerMiddleware: ProducerMiddleware = async (
  topic,
  eventName,
  payload,
  headers,
  next,
) => {
  const { span, headers: tracedHeaders } = MessagingTracer.createProducerSpan(
    topic,
    eventName,
    headers,
  );
  try {
    const event = await next(topic, eventName, payload, tracedHeaders);
    MessagingTracer.finishSpan(span);
    return event;
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    MessagingTracer.finishSpan(span, error);
    throw error;
  }
};

export const loggingProducerMiddleware: ProducerMiddleware = async (
  topic,
  eventName,
  payload,
  headers,
  next,
) => {
  console.log(`[ProducerMiddleware] Outgoing Event -> ${topic}:${eventName} [CorrID: ${headers?.correlationId || 'N/A'}]`);
  return next(topic, eventName, payload, headers);
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
      await client.publishEvent(`${topic}-dlq`, `${event.eventName}.DLQ`, {
        failedEvent: event,
        error: String(err),
      }, event.headers);
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
