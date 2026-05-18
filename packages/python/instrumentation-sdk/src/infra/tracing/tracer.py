from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
import os

def init_tracer(service_name: str, env: str = "dev"):
    resource = Resource.create({
        "service.name": service_name,
        "deployment.env": env,
        "service.version": "0.1.0",
        "language.package-name": "instrumentation-sdk"
    })
    
    provider = TracerProvider(resource=resource)
    
    if os.getenv("SKIP_CONSOLE_EXPORTER") != "true":
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        
    if os.getenv("SKIP_OTLP_EXPORTER") != "true":
        try:
            otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(otlp_processor)
        except Exception:
            pass
        
    trace.set_tracer_provider(provider)


def get_tracer():
    return trace.get_tracer("instrumentation-sdk")
