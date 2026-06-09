import pytest
from pytrace_features.flow.service import FlowService
from pytrace_infra.adapters.sqlite_store import SQLiteStore

def test_flow_service_renders(capsys):
    store = SQLiteStore(":memory:")
    # Populate a trace and root spans
    store.insert_trace("t_test", 1000, 2000)
    store.insert_span("s_root", "t_test", None, "handle_request", 1000, 2000, 1000000, "api-service")
    store.insert_span("s_child", "t_test", "s_root", "call_llm", 1100, 1900, 800000, "api-service")

    service = FlowService(store)
    service.render_tree([])
    captured = capsys.readouterr()
    assert "handle_request" in captured.out
    assert "call_llm" in captured.out
