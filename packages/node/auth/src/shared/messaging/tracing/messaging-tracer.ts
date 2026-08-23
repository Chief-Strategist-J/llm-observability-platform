import { KafkaHeaders, KafkaEvent, RequestContextHolder } from '@observability/core';

export interface MessagingTraceSpan {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  operation: 'publish' | 'process';
  topic: string;
  eventName: string;
  startTime: number;
  attributes: Record<string, unknown>;
  status: 'ok' | 'error';
  error?: Error;
}

export class MessagingTracer {
  public static generateTraceId(): string {
    const hexChars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < 32; i++) {
      result += hexChars[Math.floor(Math.random() * 16)];
    }
    return result;
  }

  public static generateSpanId(): string {
    const hexChars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < 16; i++) {
      result += hexChars[Math.floor(Math.random() * 16)];
    }
    return result;
  }

  public static parseTraceparent(traceparent?: string): { traceId: string; parentSpanId?: string } {
    if (!traceparent) {
      return { traceId: this.generateTraceId() };
    }
    const parts = traceparent.split('-');
    if (parts.length >= 3 && parts[1] && parts[2]) {
      return { traceId: parts[1], parentSpanId: parts[2] };
    }
    return { traceId: this.generateTraceId() };
  }

  public static formatTraceparent(traceId: string, spanId: string): string {
    return `00-${traceId}-${spanId}-01`;
  }

  public static createProducerSpan(
    topic: string,
    eventName: string,
    existingHeaders?: KafkaHeaders,
  ): { span: MessagingTraceSpan; headers: KafkaHeaders } {
    const activeCtx = RequestContextHolder.get();

    const traceparentHeader = existingHeaders?.traceparent || activeCtx.traceparent;
    const parsed = this.parseTraceparent(traceparentHeader);
    const spanId = this.generateSpanId();
    const newTraceparent = this.formatTraceparent(parsed.traceId, spanId);

    const headers: KafkaHeaders = {
      ...existingHeaders,
      traceparent: newTraceparent,
      tracestate: existingHeaders?.tracestate || activeCtx.tracestate || 'rojo=1',
      correlationId: existingHeaders?.correlationId || activeCtx.correlationId,
      requestId: existingHeaders?.requestId || activeCtx.requestId,
      idempotencyKey: existingHeaders?.idempotencyKey || activeCtx.idempotencyKey,
      tenantId: existingHeaders?.tenantId || activeCtx.tenantId || 'tenant-default',
    };

    const span: MessagingTraceSpan = {
      traceId: parsed.traceId,
      spanId,
      parentSpanId: parsed.parentSpanId,
      operation: 'publish',
      topic,
      eventName,
      startTime: Date.now(),
      attributes: {
        'messaging.system': 'kafka',
        'messaging.destination': topic,
        'messaging.kafka.event_name': eventName,
        'messaging.operation': 'publish',
        'messaging.correlation_id': headers.correlationId,
        'messaging.request_id': headers.requestId,
        'messaging.idempotency_key': headers.idempotencyKey,
        'messaging.tenant_id': headers.tenantId,
      },
      status: 'ok',
    };

    console.log(
      `[MessagingTracer] PRODUCE SPAN STARTED [traceId=${span.traceId}, spanId=${span.spanId}, reqId=${headers.requestId}] -> ${topic}:${eventName}`,
    );

    return { span, headers };
  }

  public static createConsumerSpan(
    event: KafkaEvent<unknown>,
    topic: string,
  ): MessagingTraceSpan {
    const parsed = this.parseTraceparent(event.headers?.traceparent);
    const spanId = this.generateSpanId();

    const span: MessagingTraceSpan = {
      traceId: parsed.traceId,
      spanId,
      parentSpanId: parsed.parentSpanId,
      operation: 'process',
      topic,
      eventName: event.eventName,
      startTime: Date.now(),
      attributes: {
        'messaging.system': 'kafka',
        'messaging.destination': topic,
        'messaging.kafka.event_name': event.eventName,
        'messaging.operation': 'process',
        'messaging.message_id': event.id,
        'messaging.correlation_id': event.headers?.correlationId,
        'messaging.request_id': event.headers?.requestId,
        'messaging.idempotency_key': event.headers?.idempotencyKey,
        'messaging.tenant_id': event.headers?.tenantId,
      },
      status: 'ok',
    };

    console.log(
      `[MessagingTracer] CONSUME SPAN STARTED [traceId=${span.traceId}, spanId=${span.spanId}, reqId=${event.headers?.requestId || 'N/A'}] -> ${event.eventName}`,
    );

    return span;
  }

  public static finishSpan(span: MessagingTraceSpan, error?: Error): void {
    const durationMs = Date.now() - span.startTime;
    if (error) {
      span.status = 'error';
      span.error = error;
      console.error(
        `[MessagingTracer] SPAN FAILED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> Error: ${error.message}`,
      );
    } else {
      console.log(
        `[MessagingTracer] SPAN COMPLETED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> ${span.topic}:${span.eventName}`,
      );
    }
  }
}
