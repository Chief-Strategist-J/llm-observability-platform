import { trace, context, type Tracer, SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import { NodeTracerProvider, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { AsyncLocalStorageContextManager } from '@opentelemetry/context-async-hooks';

export { SpanKind, SpanStatusCode, trace, context, ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION, type Span, type Tracer };

process.env.OTEL_EXPORTER_OTLP_PROTOCOL = 'http/json';

let providerInitialized = false;

export function initNodeTracing(serviceName = 'observability-service', serviceVersion = '1.0.0'): void {
  if (providerInitialized) return;

  const contextManager = new AsyncLocalStorageContextManager();
  contextManager.enable();
  context.setGlobalContextManager(contextManager);

  const resource = new Resource({
    [ATTR_SERVICE_NAME]: serviceName,
    [ATTR_SERVICE_VERSION]: serviceVersion,
  });

  const otlpEndpoint = process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:31417/v1/traces';

  const exporter = new OTLPTraceExporter({
    url: otlpEndpoint,
  });

  const provider = new NodeTracerProvider({
    resource,
    spanProcessors: [
      new SimpleSpanProcessor(exporter),
    ],
  });

  provider.register();
  providerInitialized = true;
}

export function getTracer(serviceName = 'observability-service', serviceVersion = '1.0.0'): Tracer {
  if (!providerInitialized) {
    initNodeTracing(serviceName, serviceVersion);
  }
  return trace.getTracer(serviceName, serviceVersion);
}

export async function withSpan<T>(
  name: string,
  fn: (span: Span) => Promise<T>,
  options: { kind?: SpanKind; attributes?: Record<string, string | number | boolean>; serviceName?: string } = {}
): Promise<T> {
  const tracer = getTracer(options.serviceName);
  return tracer.startActiveSpan(
    name,
    { kind: options.kind ?? SpanKind.INTERNAL, attributes: options.attributes },
    async (span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : String(error),
        });
        if (error instanceof Error) {
          span.recordException(error);
        }
        span.setAttribute('error', true);
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
