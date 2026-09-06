import { createKafkaClient, CentralizedKafkaClient, KafkaHeaders, KafkaEvent, TypedEventProducer } from '@observability/shared-infra';
import { AUTH_KAFKA_TOPICS } from '../topics/auth-topics';

export class AuthEventProducer {
  private client: CentralizedKafkaClient;
  private producer: TypedEventProducer;

  constructor() {
    this.client = createKafkaClient('auth-service-producer');
    this.producer = new TypedEventProducer(this.client);
  }

  public async init(): Promise<void> {
    await this.client.connect();
  }

  public publishUserSignedIn(
    payload: { userId: string; email: string; orgId: string },
    headers?: KafkaHeaders,
  ): Promise<KafkaEvent<typeof payload>> {
    return this.producer.publish(
      AUTH_KAFKA_TOPICS.AUTH_EVENTS,
      'USER_SIGNED_IN',
      payload,
      headers,
    );
  }

  public publishUserSignedUp(
    payload: { userId: string; email: string; orgId: string },
    headers?: KafkaHeaders,
  ): Promise<KafkaEvent<typeof payload>> {
    return this.producer.publish(
      AUTH_KAFKA_TOPICS.AUTH_EVENTS,
      'USER_SIGNED_UP',
      payload,
      headers,
    );
  }
}
