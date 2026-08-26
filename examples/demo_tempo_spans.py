#!/usr/bin/env python3
import time
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

def main():
    print("Initializing OpenTelemetry Tracer Provider...")
    resource = Resource(attributes={
        SERVICE_NAME: "demo-autoinstrumentation-service"
    })
    
    provider = TracerProvider(resource=resource)
    
    # Export spans to Tempo gRPC endpoint (port 4317)
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:31418", insecure=True)
    processor = BatchSpanProcessor(otlp_exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    tracer = trace.get_tracer("demo.tracer")

    print("Generating test spans for Grafana Tempo...")
    with tracer.start_as_current_span("parent-operation-llm-workflow") as parent:
        parent.set_attribute("workflow.name", "demo-llm-pipeline")
        parent.set_attribute("workflow.status", "success")
        time.sleep(0.1)

        with tracer.start_as_current_span("llm-prompt-formatting") as child1:
            child1.set_attribute("prompt.template", "Summarize user input")
            child1.set_attribute("tokens.prompt", 42)
            time.sleep(0.05)

        with tracer.start_as_current_span("llm-inference-call") as child2:
            child2.set_attribute("llm.provider", "openai")
            child2.set_attribute("llm.model", "gpt-4o")
            child2.set_attribute("tokens.completion", 128)
            time.sleep(0.2)

        with tracer.start_as_current_span("post-processing-eval") as child3:
            child3.set_attribute("eval.passed", True)
            time.sleep(0.03)

    print("Flushing spans to Tempo...")
    provider.shutdown()
    print("Done! Spans emitted.")

if __name__ == "__main__":
    main()
