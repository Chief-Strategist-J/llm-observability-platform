import { createKafkaClient, CentralizedKafkaClient, TypedEventConsumer } from '@observability/shared-infra';
import { AUTH_KAFKA_TOPICS } from '../topics/auth-topics';
import { AuthEventHandlerRegistry } from '../handlers/auth-event.handlers';

export class AuthEventConsumer {
  private client: CentralizedKafkaClient;
  private consumer: TypedEventConsumer;
  private registry: AuthEventHandlerRegistry;
  private unsubscribeFns: Array<() => void> = [];

  constructor(registry?: AuthEventHandlerRegistry) {
    this.client = createKafkaClient('auth-service-consumer');
    this.registry = registry || new AuthEventHandlerRegistry();
    this.consumer = new TypedEventConsumer(this.client);
  }

  public async init(): Promise<void> {
    await this.client.connect();
    this.subscribe();
  }

  private subscribe(): void {
    const topic = AUTH_KAFKA_TOPICS.AUTH_EVENTS;
    const unsub = this.consumer.subscribe(topic, (event) =>
      this.registry.dispatch(event, topic),
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
