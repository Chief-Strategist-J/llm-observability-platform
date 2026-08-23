import { trace, type Tracer, SpanKind, SpanStatusCode, type Span } from '@opentelemetry/api';
import { NodeTracerProvider, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { AUTH_CONSTANTS } from '../../shared/constants/auth.constants';

let providerInitialized = false;

export function initAuthTracing(): void {
  if (providerInitialized) return;

  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: AUTH_CONSTANTS.SERVICE_NAME,
    [ATTR_SERVICE_VERSION]: AUTH_CONSTANTS.SERVICE_VERSION,
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

export function getTracer(): Tracer {
  if (!providerInitialized) {
    initAuthTracing();
  }
  return trace.getTracer(AUTH_CONSTANTS.SERVICE_NAME, AUTH_CONSTANTS.SERVICE_VERSION);
}

export async function withSpan<T>(
  name: string,
  fn: (span: Span) => Promise<T>,
  options: { kind?: SpanKind; attributes?: Record<string, string | number | boolean> } = {}
): Promise<T> {
  const tracer = getTracer();
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
        throw error;
      } finally {
        span.end();
      }
    }
  );
}
