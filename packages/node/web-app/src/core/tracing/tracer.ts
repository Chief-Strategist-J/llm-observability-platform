import { WebTracerProvider, BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { trace, ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@observability/shared-infra';

let providerInitialized = false;

export function initOpenTelemetryTracer(): void {
  if (providerInitialized) return;

  if (typeof window === 'undefined') {
    import('@observability/shared-infra/tracing').then(({ initNodeTracing }) => {
      initNodeTracing('web-app', '0.1.0');
    }).catch(() => {});
    providerInitialized = true;
    return;
  }

  const resource = resourceFromAttributes({
    [ATTR_SERVICE_NAME]: 'web-app',
    [ATTR_SERVICE_VERSION]: '0.1.0',
  });

  const otlpEndpoint = process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:31417/v1/traces';

  const exporter = new OTLPTraceExporter({
    url: otlpEndpoint,
  });

  const provider = new WebTracerProvider({
    resource,
    spanProcessors: [new BatchSpanProcessor(exporter)],
  });

  provider.register();
  providerInitialized = true;
}

export function getOpenTelemetryTracer(name = 'web-app') {
  return trace.getTracer(name, '0.1.0');
}
