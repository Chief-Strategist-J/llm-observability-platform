import { type Span, SpanKind, SpanStatusCode, withSpan } from './tracer';
import type { KafkaEvent } from '../kafka/kafka-client';
import { z } from 'zod';
import { TRACING_CONSTANTS } from './constants';

export * from './constants';

export abstract class BaseTracedKafkaHandler<T = unknown> {
  public abstract readonly eventName: string;

  public async handle(event: KafkaEvent<T>, topic?: string): Promise<void> {
    const spanName = `Handler ${this.eventName}`;
    await withSpan(spanName, async (span: Span) => {
      span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_EVENT_NAME, event.eventName);
      span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_EVENT_ID, event.id);
      if (topic) {
        span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_TOPIC, topic);
      }
      if (event.headers?.tenantId) {
        span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_TENANT_ID, event.headers.tenantId);
      }
      const p = event.payload as any;
      if (p?.userId) span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_USER_ID, p.userId);
      if (p?.orgId) span.setAttribute(TRACING_CONSTANTS.ATTR_CQRS_ORG_ID, p.orgId);

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
      span.setAttribute(TRACING_CONSTANTS.ATTR_HTTP_ROUTE, routeName);
      const parseResult = schema.safeParse(rawParams);

      if (!parseResult.success) {
        const formattedErrors = parseResult.error.format();
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: `Validation Failed for ${routeName}`,
        });
        span.setAttribute(TRACING_CONSTANTS.ATTR_VALIDATION_STATUS, TRACING_CONSTANTS.STATUS_VALIDATION_FAILED);
        span.setAttribute(TRACING_CONSTANTS.ATTR_VALIDATION_ERRORS, JSON.stringify(formattedErrors));
        return {
          success: false,
          error: TRACING_CONSTANTS.ERROR_INVALID_REQUEST,
          details: formattedErrors,
        };
      }

      span.setAttribute(TRACING_CONSTANTS.ATTR_VALIDATION_STATUS, TRACING_CONSTANTS.STATUS_SUCCESS);
      const data = await handler(parseResult.data, span);
      return { success: true, data };
    },
    { kind: SpanKind.SERVER }
  );
}
