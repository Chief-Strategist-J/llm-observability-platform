import { type Span, SpanKind, SpanStatusCode, withSpan } from './tracer';
import type { KafkaEvent } from '../kafka/kafka-client';
import { z } from 'zod';

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

export async function withTracedValidation<TParams, TResult>(
  routeName: string,
  schema: z.ZodType<TParams>,
  rawParams: unknown,
  handler: (validatedParams: TParams, span: Span) => Promise<TResult>
): Promise<{ success: true; data: TResult } | { success: false; error: string; details: unknown }> {
  return withSpan(
    `Route ${routeName}`,
    async (span) => {
      span.setAttribute('http.route', routeName);
      const parseResult = schema.safeParse(rawParams);

      if (!parseResult.success) {
        const formattedErrors = parseResult.error.format();
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: `Validation Failed for ${routeName}`,
        });
        span.setAttribute('validation.status', 'validation_failed');
        span.setAttribute('validation.errors', JSON.stringify(formattedErrors));
        return {
          success: false,
          error: 'Invalid request parameters',
          details: formattedErrors,
        };
      }

      span.setAttribute('validation.status', 'success');
      const data = await handler(parseResult.data, span);
      return { success: true, data };
    },
    { kind: SpanKind.SERVER }
  );
}
