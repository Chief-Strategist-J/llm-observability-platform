import { KafkaEvent } from '@observability/core';

export abstract class BaseTracedKafkaHandler<T = unknown> {
  public abstract readonly eventName: string;

  public abstract handle(event: KafkaEvent<T>, topic: string): Promise<void>;
}
