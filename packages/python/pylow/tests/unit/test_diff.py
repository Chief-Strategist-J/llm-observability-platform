import pytest
from pytrace_features.diff.service import DiffService
from pytrace_infra.adapters.sqlite_store import SQLiteStore

def test_diff_service_renders(capsys):
    store = SQLiteStore(":memory:")
    service = DiffService(store)
    service.compare("v1.2", "v1.3")
    captured = capsys.readouterr()
    assert "REGRESSIONS" in captured.out
    assert "NEW CALLS in v1.3" in captured.out

