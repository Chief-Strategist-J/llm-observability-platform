import { CentralizedKafkaClient, KafkaEvent, KafkaEventHandler } from '../../infra/messaging/client-factory';
import {
  ConsumerMiddlewarePipeline,
  idempotencyConsumerMiddleware,
  tracingConsumerMiddleware,
  dlqConsumerMiddleware,
  loggingConsumerMiddleware,
} from '../middleware/consumer-pipeline';

export class TypedEventConsumer {
  private pipeline: ConsumerMiddlewarePipeline;

  constructor(private kafkaClient: CentralizedKafkaClient) {
    this.pipeline = new ConsumerMiddlewarePipeline();
    this.pipeline
      .use(dlqConsumerMiddleware(this.kafkaClient))
      .use(tracingConsumerMiddleware)
      .use(loggingConsumerMiddleware)
      .use(idempotencyConsumerMiddleware);
  }

  public subscribe<T = unknown>(
    topic: string,
    handler: KafkaEventHandler<T>,
  ): () => void {
    const wrappedHandler: KafkaEventHandler<T> = (event: KafkaEvent<T>) => {
      return this.pipeline.execute(event, topic, (ev) => Promise.resolve(handler(ev)));
    };

    return this.kafkaClient.subscribeToTopic(topic, wrappedHandler);
  }
}
