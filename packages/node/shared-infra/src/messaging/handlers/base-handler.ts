import type { KafkaEvent } from '../../infra/messaging/client-factory';

export interface IEventHandler<T = unknown> {
  eventName: string;
  handle(event: KafkaEvent<T>): Promise<void>;
}

export abstract class BaseEventHandler<T = unknown> implements IEventHandler<T> {
  abstract readonly eventName: string;

  abstract process(payload: T, event: KafkaEvent<T>): Promise<void>;

  public async handle(event: KafkaEvent<T>): Promise<void> {
    console.log(
      `[EventHandler:${this.constructor.name}] Handling ${event.eventName} [ID: ${event.id}]`,
    );
    await this.process(event.payload, event);
  }
}
