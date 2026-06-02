import { WebTracerProvider } from "@opentelemetry/sdk-trace-web";
import { BatchSpanProcessor } from "@opentelemetry/sdk-trace-web";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { Resource } from "@opentelemetry/resources";
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from "@opentelemetry/semantic-conventions";
import { trace } from "@opentelemetry/api";

export function initTracer(): void {
  const resource = new Resource({
    [SEMRESATTRS_SERVICE_NAME]: "node.webrtc-client",
    [SEMRESATTRS_SERVICE_VERSION]: "1.0.0",
  });

  const provider = new WebTracerProvider({ resource });

  const otlpEndpoint = import.meta.env["VITE_OTEL_ENDPOINT"] as string | undefined;
  if (otlpEndpoint) {
    provider.addSpanProcessor(
      new BatchSpanProcessor(new OTLPTraceExporter({ url: otlpEndpoint }))
    );
  }

  provider.register();
}

export function getTracer() {
  return trace.getTracer("webrtc-client", "1.0.0");
}
