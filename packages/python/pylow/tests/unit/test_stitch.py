import pytest
from pytrace_features.stitch.service import StitchService
from pytrace_infra.adapters.sqlite_store import SQLiteStore

def test_stitch_service_renders(capsys):
    store = SQLiteStore(":memory:")
    service = StitchService(store)
    service.stitch_traces(["api", "worker"])
    captured = capsys.readouterr()
    assert "REQUEST trace-id" in captured.out
    assert "api-service" in captured.out

