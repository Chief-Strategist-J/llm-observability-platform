import { createKafkaClient, CentralizedKafkaClient, KafkaEvent } from '@observability/core';
import { AUTH_KAFKA_TOPICS } from '../topics/auth-topics';
import { AuthEventHandlerRegistry } from '../handlers/auth-event.handlers';
import {
  ConsumerMiddlewarePipeline,
  tracingConsumerMiddleware,
  loggingConsumerMiddleware,
  dlqConsumerMiddleware,
  idempotencyConsumerMiddleware,
  retryConsumerMiddleware,
} from '../middleware/messaging-middleware';

export class AuthEventConsumer {
  private client: CentralizedKafkaClient;
  private registry: AuthEventHandlerRegistry;
  private pipeline: ConsumerMiddlewarePipeline;
  private unsubscribeFns: Array<() => void> = [];

  constructor(registry?: AuthEventHandlerRegistry) {
    this.client = createKafkaClient('auth-service-consumer');
    this.registry = registry || new AuthEventHandlerRegistry();
    this.pipeline = new ConsumerMiddlewarePipeline()
      .use(loggingConsumerMiddleware)
      .use(idempotencyConsumerMiddleware)
      .use(dlqConsumerMiddleware(this.client))
      .use(retryConsumerMiddleware(3, 50))
      .use(tracingConsumerMiddleware);
  }

  public async init(): Promise<void> {
    await this.client.connect();
    this.subscribe();
  }

  private subscribe(): void {
    const topic = AUTH_KAFKA_TOPICS.AUTH_EVENTS;
    const unsub = this.client.subscribeToTopic(topic, (event: KafkaEvent<any>) =>
      this.pipeline.execute(event, topic, (ev, top) => this.registry.dispatch(ev, top)),
    );
    this.unsubscribeFns.push(unsub);
  }

  public async stop(): Promise<void> {
    for (const unsub of this.unsubscribeFns) {
      unsub();
    }
    this.unsubscribeFns = [];
  }
}
