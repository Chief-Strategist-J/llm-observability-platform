import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


def init_tracer() -> trace.Tracer:
    resource = Resource.create(
        {
            SERVICE_NAME: "python.webrtc-signaling",
            SERVICE_VERSION: "1.0.0",
            "deployment.env": os.getenv("DEPLOYMENT_ENV", "dev"),
        }
    )
    provider = TracerProvider(resource=resource)

    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint)))

    trace.set_tracer_provider(provider)
    return trace.get_tracer("webrtc-signaling", "1.0.0")
