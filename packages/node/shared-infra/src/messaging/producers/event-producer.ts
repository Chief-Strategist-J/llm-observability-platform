import { CentralizedKafkaClient, KafkaEvent, KafkaHeaders } from '../../infra/messaging/client-factory';
import {
  ProducerMiddlewarePipeline,
  tracingProducerMiddleware,
  loggingProducerMiddleware,
  retryProducerMiddleware,
} from '../middleware/producer-pipeline';

export class TypedEventProducer {
  private pipeline: ProducerMiddlewarePipeline;

  constructor(private kafkaClient: CentralizedKafkaClient) {
    this.pipeline = new ProducerMiddlewarePipeline();
    this.pipeline
      .use(tracingProducerMiddleware)
      .use(loggingProducerMiddleware)
      .use(retryProducerMiddleware());
  }

  public publish<T = unknown>(
    topic: string,
    eventName: string,
    payload: T,
    headers?: KafkaHeaders,
  ): Promise<KafkaEvent<T>> {
    return this.pipeline.execute(
      topic,
      eventName,
      payload,
      headers,
      (t, e, p, h) => this.kafkaClient.publishEvent(t, e, p, h),
    );
  }
}
