import type { KafkaEvent, KafkaHeaders } from '../../infra/messaging/client-factory';
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
    const dispatch = (
      i: number,
      t: string,
      e: string,
      p: T,
      h?: KafkaHeaders,
    ): Promise<KafkaEvent<T>> => {
      if (i <= index) return Promise.reject(new Error('next() called multiple times in producer middleware'));
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

// --- Standard Builtin Producer Middlewares ---

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
  console.log(
    `[ProducerMiddleware] Outgoing Event -> ${topic}:${eventName} [CorrID: ${headers?.correlationId || 'N/A'}]`,
  );
  return next(topic, eventName, payload, headers);
};

export const retryProducerMiddleware = (
  maxRetries = 3,
  initialDelayMs = 100,
): ProducerMiddleware => {
  return async (topic, eventName, payload, headers, next) => {
    let attempt = 0;
    while (true) {
      try {
        return await next(topic, eventName, payload, headers);
      } catch (err) {
        attempt++;
        if (attempt >= maxRetries) throw err;
        const delay = initialDelayMs * 2 ** (attempt - 1);
        console.warn(
          `[ProducerRetryMiddleware] Attempt ${attempt}/${maxRetries} failed for ${topic}:${eventName}. Retrying in ${delay}ms...`,
        );
        await new Promise((resolve) => setTimeout(resolve, delay));
      }
    }
  };
};
