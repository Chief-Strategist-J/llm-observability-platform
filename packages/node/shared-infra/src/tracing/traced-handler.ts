import type { Span } from '@opentelemetry/api';
import type { KafkaEvent } from '../kafka/kafka-client';
import { withSpan } from './tracer';

export abstract class BaseTracedKafkaHandler<T = unknown> {
  public abstract readonly eventName: string;

  public async handle(event: KafkaEvent<T>, topic?: string): Promise<void> {
    const spanName = `Handler ${this.eventName}`;
    await withSpan(spanName, async (span: Span) => {
      span.setAttribute('cqrs.event_name', event.eventName);
      span.setAttribute('cqrs.event_id', event.id);
      if (topic) {
        span.setAttribute('cqrs.topic', topic);
      }
      if (event.headers?.tenantId) {
        span.setAttribute('cqrs.tenant_id', event.headers.tenantId);
      }
      const p = event.payload as any;
      if (p?.userId) span.setAttribute('cqrs.user_id', p.userId);
      if (p?.orgId) span.setAttribute('cqrs.org_id', p.orgId);

      await this.handlePayload(event.payload, event, span);
    });
  }

  protected abstract handlePayload(payload: T, event: KafkaEvent<T>, span: Span): Promise<void>;
}
