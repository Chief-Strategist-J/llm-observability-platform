import { createKafkaClient, CentralizedKafkaClient, KafkaHeaders, KafkaEvent } from '@observability/shared-infra';
import { AUTH_KAFKA_TOPICS } from '../topics/auth-topics';
import {
  ProducerMiddlewarePipeline,
  tracingProducerMiddleware,
  loggingProducerMiddleware,
} from '../middleware/messaging-middleware';

export class AuthEventProducer {
  private client: CentralizedKafkaClient;
  private pipeline: ProducerMiddlewarePipeline;

  constructor() {
    this.client = createKafkaClient('auth-service-producer');
    this.pipeline = new ProducerMiddlewarePipeline()
      .use(loggingProducerMiddleware)
      .use(tracingProducerMiddleware);
  }

  public async init(): Promise<void> {
    await this.client.connect();
  }

  public publishUserSignedIn(
    payload: { userId: string; email: string; orgId: string },
    headers?: KafkaHeaders,
  ): Promise<KafkaEvent<typeof payload>> {
    return this.pipeline.execute(
      AUTH_KAFKA_TOPICS.AUTH_EVENTS,
      'USER_SIGNED_IN',
      payload,
      headers,
      (topic, eventName, p, h) => this.client.publishEvent(topic, eventName, p, h),
    );
  }

  public publishUserSignedUp(
    payload: { userId: string; email: string; orgId: string },
    headers?: KafkaHeaders,
  ): Promise<KafkaEvent<typeof payload>> {
    return this.pipeline.execute(
      AUTH_KAFKA_TOPICS.AUTH_EVENTS,
      'USER_SIGNED_UP',
      payload,
      headers,
      (topic, eventName, p, h) => this.client.publishEvent(topic, eventName, p, h),
    );
  }
}
