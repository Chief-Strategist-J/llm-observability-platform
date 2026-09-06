import os
import sys
from pathlib import Path
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

sdk_root = Path(__file__).resolve().parents[3]
if str(sdk_root) not in sys.path:
    sys.path.insert(0, str(sdk_root))

from config.infra.env_config import service_config

_PROVIDER_INITIALIZED = False

def init_tracer(service_name: str | None = None, env: str | None = None) -> None:
    global _PROVIDER_INITIALIZED
    if _PROVIDER_INITIALIZED:
        return
    svc_name = service_name or service_config.default_service_name
    deployment_env = env or service_config.app_env
    
    resource = Resource.create({
        "service.name": svc_name,
        "deployment.env": deployment_env,
        "service.version": service_config.service_version,
        "language.package-name": "instrumentation-sdk"
    })
    
    provider = TracerProvider(resource=resource)
    
    if service_config.skip_console_exporter.lower() != "true":
        processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(processor)
        
    if service_config.skip_otlp_exporter.lower() != "true":
        try:
            otlp_endpoint = service_config.otel_exporter_endpoint
            grpc_target = otlp_endpoint.replace("http://", "").replace("https://", "")
            otlp_exporter = OTLPSpanExporter(endpoint=grpc_target, insecure=True)
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(otlp_processor)
        except Exception:
            pass
        
    trace.set_tracer_provider(provider)
    _PROVIDER_INITIALIZED = True

def get_tracer():
    init_tracer()
    return trace.get_tracer(service_config.default_service_name)
