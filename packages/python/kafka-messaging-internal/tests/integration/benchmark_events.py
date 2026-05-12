import asyncio
import time
import uuid
import os
from datetime import datetime, timezone
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# Configure tracing for the benchmark (no console exporter to avoid spam)
provider = TracerProvider()
trace.set_tracer_provider(provider)

from kafka_messaging_internal.shared.di.container import DIContainer
from kafka_messaging_internal.features.event_processing.service import EventProcessingService
from kafka_messaging_internal.infra.adapters.postgresql.postgres_adapter import PostgresAdapter
from kafka_messaging_internal.shared.ports.database_port import EventRecord

# Monkey-patch OTEL _Span to support record_error
from opentelemetry.sdk.trace import _Span
if not hasattr(_Span, "record_error"):
    _Span.record_error = _Span.record_exception

async def run_benchmark():
    # We will use the PostgresAdapter for real DB interaction
    config = {
        "POSTGRES_DSN": os.environ.get("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/postgres")
    }
    db_adapter = PostgresAdapter(config)
    
    service = EventProcessingService(db_adapter)
    
    # Generate a large batch of events
    batch_size = 5000
    events = []
    for i in range(batch_size):
        events.append({
            "event_id": str(uuid.uuid4()),
            "topic": "benchmark-topic",
            "partition": 0,
            "offset": i,
            "key": str(uuid.uuid4()),
            "value": {"test": "data", "index": i},
            "timestamp": datetime.now(timezone.utc)
        })
        
    print(f"Starting batch process for {batch_size} events...")
    
    start_time = time.time()
    
    # Run the batch
    results = await service.process_events_batch(events)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Processed {batch_size} events in {duration:.2f} seconds.")
    print(f"Throughput: {batch_size / duration:.2f} events/second.")
    
    success_count = sum(1 for r in results if r["success"])
    print(f"Successes: {success_count}/{batch_size}")
    
    await db_adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
