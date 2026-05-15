from contextlib import contextmanager
import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

_PROVIDER_SET = False


def init_tracer() -> None:
    global _PROVIDER_SET
    if _PROVIDER_SET:
        return
    resource = Resource.create({"service.name": "python.queue-embedding-worker", "service.version": "0.1.0"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    trace.set_tracer_provider(provider)
    _PROVIDER_SET = True


@contextmanager
def worker_span(name: str, feature_name: str, api_version: str = "v1"):
    init_tracer()
    tracer = trace.get_tracer("queue-embedding-worker")
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("service.name", "python.queue-embedding-worker")
        span.set_attribute("service.version", "0.1.0")
        span.set_attribute("feature.name", feature_name)
        span.set_attribute("api.version", api_version)
        span.set_attribute("deployment.env", os.getenv("DEPLOYMENT_ENV", "dev"))
        span.set_attribute("host.name", os.uname().nodename)
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))
            raise
