import sys
import os
import asyncio
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PACKAGE_DIR)

import src as instrumentation_sdk

class ConsoleSpanReporter(instrumentation_sdk.SpanReporter):
    def report(self, span_data: dict) -> None:
        print(f"[SpanReporter] Span captured: id={span_data.get('span_id')} service={span_data.get('service_name')} endpoint={span_data.get('endpoint')} latency={span_data.get('latency_ms_total')}ms status={span_data.get('status')}")

    async def report_async(self, span_data: dict) -> None:
        print(f"[SpanReporter Async] Span captured: id={span_data.get('span_id')} service={span_data.get('service_name')} endpoint={span_data.get('endpoint')} latency={span_data.get('latency_ms_total')}ms status={span_data.get('status')}")

instrumentation_sdk.set_reporter(ConsoleSpanReporter())

@instrumentation_sdk.llm_observe(service="llm-observability-platform", endpoint="/v1/chat/completions")
def sync_chat_completion(prompt: str) -> str:
    time.sleep(0.125)
    return f"Response to: {prompt}"

@instrumentation_sdk.llm_observe(service="llm-observability-platform", endpoint="/v1/embeddings")
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

    print("Done! Both real instrumentation SDK spans were captured and processed.")

if __name__ == "__main__":
    main()
