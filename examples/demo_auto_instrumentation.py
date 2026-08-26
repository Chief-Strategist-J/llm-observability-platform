#!/usr/bin/env python3
import os
import sys
import time

# Add the SDK src path to sys.path
sdk_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "python", "instrumentation-sdk", "src"))
sdk_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "packages", "python", "instrumentation-sdk"))
if sdk_src not in sys.path:
    sys.path.insert(0, sdk_src)
if sdk_root not in sys.path:
    sys.path.insert(0, sdk_root)

# OpenTelemetry Standard Setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Import SDK Auto-Instrumentation
from features.auto_instrumentation.index import init_auto_instrumentation, trigger_test_call

def setup_tracer():
    print("[1] Initializing OpenTelemetry Tracer Provider...")
    resource = Resource(attributes={SERVICE_NAME: "llm-auto-instrumented-app"})
    provider = TracerProvider(resource=resource)
    
    # Send spans directly to OTEL Collector gRPC (port 31418) or Tempo (port 4317)
    exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return provider

def main():
    provider = setup_tracer()
    tracer = trace.get_tracer("auto.instrumentation.demo")

    print("[2] Initializing SDK Auto-Instrumentation (zero-code patching)...")
    init_auto_instrumentation()

    print("[3] Simulating user request with auto-instrumented LLM HTTP call...")
    with tracer.start_as_current_span("user-request-handler") as span:
        span.set_attribute("user.id", "usr_998234")
        
        # Trigger an auto-instrumented request via HTTP client patcher
        import asyncio
        res = asyncio.run(trigger_test_call(method="httpx", provider="openai"))
        print(f"    - Intercepted call output: {res}")
        time.sleep(0.1)

    print("[4] Flushing spans to Grafana Tempo...")
    provider.shutdown()
    print("Done! Check Grafana Tempo trace explorer for service 'llm-auto-instrumented-app'.")

if __name__ == "__main__":
    main()
