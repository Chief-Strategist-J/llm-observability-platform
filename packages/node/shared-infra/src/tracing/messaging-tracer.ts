import { SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import { getTracer } from './tracer';

export interface CentralKafkaHeaders {
  requestId?: string;
  correlationId?: string;
  idempotencyKey?: string;
  tenantId?: string;
  traceparent?: string;
  tracestate?: string;
  [key: string]: string | undefined;
}

export interface CentralKafkaEvent<T = unknown> {
  id: string;
  eventName: string;
  payload: T;
  headers?: CentralKafkaHeaders;
}

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

export class CentralMessagingTracer {
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
    existingHeaders?: CentralKafkaHeaders,
    serviceName = 'observability-service',
  ): { span: MessagingTraceSpan; headers: CentralKafkaHeaders } {
    const tracer = getTracer(serviceName);
    const parsed = this.parseTraceparent(existingHeaders?.traceparent);

    const otelSpan = tracer.startSpan(`Kafka PRODUCE ${eventName}`, {
      kind: SpanKind.PRODUCER,
      attributes: {
        'messaging.system': 'kafka',
        'messaging.destination': topic,
        'messaging.kafka.event_name': eventName,
        'messaging.operation': 'publish',
        'messaging.correlation_id': existingHeaders?.correlationId || '',
        'messaging.request_id': existingHeaders?.requestId || '',
        'messaging.tenant_id': existingHeaders?.tenantId || 'tenant-default',
      },
    });

    const spanContext = otelSpan.spanContext();
    const spanId = spanContext.spanId;
    const traceId = spanContext.traceId;
    const newTraceparent = this.formatTraceparent(traceId, spanId);

    const headers: CentralKafkaHeaders = {
      ...existingHeaders,
      traceparent: newTraceparent,
      tracestate: existingHeaders?.tracestate || 'rojo=1',
      correlationId: existingHeaders?.correlationId,
      requestId: existingHeaders?.requestId,
      idempotencyKey: existingHeaders?.idempotencyKey,
      tenantId: existingHeaders?.tenantId || 'tenant-default',
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
      `[CentralMessagingTracer] PRODUCE SPAN STARTED [traceId=${span.traceId}, spanId=${span.spanId}] -> ${topic}:${eventName}`,
    );

    return { span, headers };
  }

  public static createConsumerSpan(
    event: CentralKafkaEvent<unknown>,
    topic: string,
    serviceName = 'observability-service',
  ): MessagingTraceSpan {
    const tracer = getTracer(serviceName);
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
      `[CentralMessagingTracer] CONSUME SPAN STARTED [traceId=${span.traceId}, spanId=${span.spanId}] -> ${event.eventName}`,
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
        `[CentralMessagingTracer] SPAN FAILED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> Error: ${error.message}`,
      );
    } else {
      span.otelSpan.setStatus({ code: SpanStatusCode.OK });
      console.log(
        `[CentralMessagingTracer] SPAN COMPLETED [traceId=${span.traceId}, spanId=${span.spanId}] (${durationMs}ms) -> ${span.topic}:${span.eventName}`,
      );
    }
    span.otelSpan.end();
  }
}
