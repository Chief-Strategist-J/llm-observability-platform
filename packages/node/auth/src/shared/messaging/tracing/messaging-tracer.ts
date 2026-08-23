import { trace, SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import { KafkaHeaders, KafkaEvent, RequestContextHolder } from '@observability/core';
import { getTracer } from '../../../infra/tracing/tracer';

export interface MessagingTraceSpan {
  otelSpan: Span;
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  operation: 'publish' | 'process';
  topic: string;
  eventName: string;
  startTime: number;
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
    const tracer = getTracer();
    const activeCtx = RequestContextHolder.get();

    const traceparentHeader = existingHeaders?.traceparent || activeCtx.traceparent;
    const parsed = this.parseTraceparent(traceparentHeader);

    const otelSpan = tracer.startSpan(`Kafka PRODUCE ${eventName}`, {
      kind: SpanKind.PRODUCER,
      attributes: {
        'messaging.system': 'kafka',
        'messaging.destination': topic,
        'messaging.kafka.event_name': eventName,
        'messaging.operation': 'publish',
        'messaging.correlation_id': existingHeaders?.correlationId || activeCtx.correlationId || '',
        'messaging.request_id': existingHeaders?.requestId || activeCtx.requestId || '',
        'messaging.tenant_id': existingHeaders?.tenantId || activeCtx.tenantId || 'tenant-default',
      },
    });

    const spanContext = otelSpan.spanContext();
    const spanId = spanContext.spanId;
    const traceId = spanContext.traceId;
    const newTraceparent = this.formatTraceparent(traceId, spanId);

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
      otelSpan,
      traceId,
      spanId,
      parentSpanId: parsed.parentSpanId,
      operation: 'publish',
      topic,
      eventName,
      startTime: Date.now(),
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
    const tracer = getTracer();
    const parsed = this.parseTraceparent(event.headers?.traceparent);

    const otelSpan = tracer.startSpan(`Kafka CONSUMER ${event.eventName}`, {
      kind: SpanKind.CONSUMER,
      attributes: {
        'messaging.system': 'kafka',
        'messaging.destination': topic,
        'messaging.kafka.event_name': event.eventName,
        'messaging.operation': 'process',
        'messaging.message_id': event.id,
        'messaging.correlation_id': event.headers?.correlationId || '',
        'messaging.request_id': event.headers?.requestId || '',
        'messaging.tenant_id': event.headers?.tenantId || '',
      },
    });

    const spanContext = otelSpan.spanContext();

    const span: MessagingTraceSpan = {
      otelSpan,
      traceId: spanContext.traceId,
      spanId: spanContext.spanId,
      parentSpanId: parsed.parentSpanId,
      operation: 'process',
      topic,
      eventName: event.eventName,
      startTime: Date.now(),
    };

    console.log(
      `[MessagingTracer] CONSUME SPAN STARTED [traceId=${span.traceId}, spanId=${span.spanId}, reqId=${event.headers?.requestId || 'N/A'}] -> ${event.eventName}`,
    );

    return span;
  }

  public static finishSpan(span: MessagingTraceSpan, error?: Error): void {
    const durationMs = Date.now() - span.startTime;
    if (error) {
      span.otelSpan.setStatus({
        code: SpanStatusCode.ERROR,
        message: error.message,
      });
      span.otelSpan.recordException(error);
      span.otelSpan.setAttribute('error', true);
      console.error(
        `[MessagingTracer] SPAN FAILED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> Error: ${error.message}`,
      );
    } else {
      span.otelSpan.setStatus({ code: SpanStatusCode.OK });
      console.log(
        `[MessagingTracer] SPAN COMPLETED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> ${span.topic}:${span.eventName}`,
      );
    }
    span.otelSpan.end();
  }
}
