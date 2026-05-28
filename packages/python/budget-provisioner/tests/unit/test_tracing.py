import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from unittest.mock import MagicMock
from budget_provisioner.features.budget_management.service import BudgetManagementService

def test_service_tracing_spans() -> None:
    current_provider = trace.get_tracer_provider()
    if hasattr(current_provider, "_delegate"):
        current_provider = current_provider._delegate
        
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    
    if hasattr(current_provider, "add_span_processor"):
        current_provider.add_span_processor(processor)
        
    db_port = MagicMock()
    redis_port = MagicMock()
    metrics_port = MagicMock()
    
    db_port.upsert_budget.return_value = MagicMock()
    
    service = BudgetManagementService(
        db_port=db_port,
        redis_port=redis_port,
        metrics_port=metrics_port
    )
    
    service.create_or_update_budget("usr-123", "gpt-4", 150.0, 900, 0.1)
    
    spans = exporter.get_finished_spans()
    assert len(spans) > 0
    span_names = [s.name for s in spans]
    assert "budget_service.create_or_update_budget" in span_names
