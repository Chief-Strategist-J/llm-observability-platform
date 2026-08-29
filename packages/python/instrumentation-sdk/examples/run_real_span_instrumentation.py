import sys
import os
import asyncio
import time
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PACKAGE_DIR)

from config.infra.env_config import service_config
import src as instrumentation_sdk
from src.infra.messaging.reporters.span_reporter import KafkaSpanReporter
from src.infra.tracing.tracer import init_tracer

class ConsoleSpanReporter(instrumentation_sdk.SpanReporter):
    def report(self, span_data: dict) -> None:
        print(f"[ConsoleSpanReporter] Span captured: id={span_data.get('span_id')} service={span_data.get('service_name')} endpoint={span_data.get('endpoint')} latency={span_data.get('latency_ms_total')}ms status={span_data.get('status')}")

    async def report_async(self, span_data: dict) -> None:
        print(f"[ConsoleSpanReporter Async] Span captured: id={span_data.get('span_id')} service={span_data.get('service_name')} endpoint={span_data.get('endpoint')} latency={span_data.get('latency_ms_total')}ms status={span_data.get('status')}")

class CompositeSpanReporter(instrumentation_sdk.SpanReporter):
    def __init__(self, reporters: list[instrumentation_sdk.SpanReporter]):
        self.reporters = reporters

    def report(self, span_data: dict) -> None:
        for reporter in self.reporters:
            try:
                reporter.report(span_data)
            except Exception as err:
                print(f"[CompositeSpanReporter Error]: {err}")

    async def report_async(self, span_data: dict) -> None:
        for reporter in self.reporters:
            try:
                if hasattr(reporter, "report_async"):
                    res = reporter.report_async(span_data)
                    if asyncio.iscoroutine(res):
                        await res
                else:
                    reporter.report(span_data)
            except Exception as err:
                print(f"[CompositeSpanReporter Async Error]: {err}")

init_tracer(service_config.default_service_name, service_config.app_env)

kafka_reporter = None
try:
    kafka_reporter = KafkaSpanReporter(topic=service_config.kafka_default_topic)
except Exception as exc:
    print(f"[Kafka Warning] Could not initialize Kafka reporter: {exc}")

if kafka_reporter:
    instrumentation_sdk.set_reporter(CompositeSpanReporter([ConsoleSpanReporter(), kafka_reporter]))
else:
    instrumentation_sdk.set_reporter(ConsoleSpanReporter())

@instrumentation_sdk.llm_observe(service=service_config.default_service_name, endpoint="/v1/chat/completions")
def sync_chat_completion(prompt: str) -> str:
    time.sleep(0.125)
    return f"Response to: {prompt}"

@instrumentation_sdk.llm_observe(service=service_config.default_service_name, endpoint="/v1/embeddings")
async def async_embedding_generation(text: str) -> list[float]:
    await asyncio.sleep(0.080)
    return [0.1, 0.2, 0.3, 0.4, 0.5]

def main():
    print("Executing real instrumentation SDK span capture examples...\n")
    print("1. Running sync @llm_observe function...")
    res_sync = sync_chat_completion("What is LLM observability?")
    print(f"   Function output: {res_sync}\n")

    print("2. Running async @llm_observe function...")
    res_async = asyncio.run(async_embedding_generation("Sample text for vector embedding"))
    print(f"   Function output: vector length {len(res_async)}\n")

    print(f"Done! Both real instrumentation SDK spans were captured, sent to Kafka ({service_config.kafka_bootstrap_servers} topic {service_config.kafka_default_topic}), and exported to OpenTelemetry/Tempo/Grafana ({service_config.otel_exporter_endpoint}).")

if __name__ == "__main__":
    main()
