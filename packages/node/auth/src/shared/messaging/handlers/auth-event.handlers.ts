import { KafkaEvent } from '@observability/core';
import { withSpan } from '@observability/core/tracing';
import { BaseTracedKafkaHandler } from './base-traced-handler';
import { AuthReadProjectionStore } from '../cqrs/projection.store';

export interface UserSignedInPayload {
  userId: string;
  email: string;
  orgId: string;
}

export interface UserSignedUpPayload {
  userId: string;
  email: string;
  orgId: string;
}

export class UserSignedInHandler extends BaseTracedKafkaHandler<UserSignedInPayload> {
  public readonly eventName = 'USER_SIGNED_IN';

  public async handle(event: KafkaEvent<UserSignedInPayload>): Promise<void> {
    await withSpan('CQRS Apply UserSignedIn Projection', async (span) => {
      span.setAttribute('cqrs.event', event.eventName);
      span.setAttribute('cqrs.user_id', event.payload.userId);
      span.setAttribute('cqrs.org_id', event.payload.orgId);
      AuthReadProjectionStore.getInstance().applyUserSignedIn({
        userId: event.payload.userId,
        email: event.payload.email,
        orgId: event.payload.orgId,
        timestamp: event.timestamp,
      });
    });
  }
}

export class UserSignedUpHandler extends BaseTracedKafkaHandler<UserSignedUpPayload> {
  public readonly eventName = 'USER_SIGNED_UP';

  public async handle(event: KafkaEvent<UserSignedUpPayload>): Promise<void> {
    await withSpan('CQRS Apply UserSignedUp Projection', async (span) => {
      span.setAttribute('cqrs.event', event.eventName);
      span.setAttribute('cqrs.user_id', event.payload.userId);
      span.setAttribute('cqrs.org_id', event.payload.orgId);
      AuthReadProjectionStore.getInstance().applyUserSignedUp({
        userId: event.payload.userId,
        email: event.payload.email,
        orgId: event.payload.orgId,
        timestamp: event.timestamp,
      });
    });
  }
}

export class AuthEventHandlerRegistry {
  private handlers = new Map<string, BaseTracedKafkaHandler<any>>();

  constructor() {
    this.register(new UserSignedInHandler());
    this.register(new UserSignedUpHandler());
  }

  public register(handler: BaseTracedKafkaHandler<any>): void {
    this.handlers.set(handler.eventName, handler);
  }

  public getHandler(eventName: string): BaseTracedKafkaHandler<any> | undefined {
    return this.handlers.get(eventName);
  }

  public async dispatch(event: KafkaEvent<any>, topic: string): Promise<void> {
    const handler = this.getHandler(event.eventName);
    if (!handler) {
      console.warn(`[AuthEventHandlerRegistry] No handler registered for event: ${event.eventName}`);
      return;
    }
    await handler.handle(event, topic);
  }
}
