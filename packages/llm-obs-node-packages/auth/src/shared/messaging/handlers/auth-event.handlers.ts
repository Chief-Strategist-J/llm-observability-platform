import { KafkaEvent } from '@observability/shared-infra';
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

  protected async handlePayload(payload: UserSignedInPayload, event: KafkaEvent<UserSignedInPayload>): Promise<void> {
    AuthReadProjectionStore.getInstance().applyUserSignedIn({
      userId: payload.userId,
      email: payload.email,
      orgId: payload.orgId,
      timestamp: event.timestamp,
    });
  }
}

export class UserSignedUpHandler extends BaseTracedKafkaHandler<UserSignedUpPayload> {
  public readonly eventName = 'USER_SIGNED_UP';

  protected async handlePayload(payload: UserSignedUpPayload, event: KafkaEvent<UserSignedUpPayload>): Promise<void> {
    AuthReadProjectionStore.getInstance().applyUserSignedUp({
      userId: payload.userId,
      email: payload.email,
      orgId: payload.orgId,
      timestamp: event.timestamp,
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
