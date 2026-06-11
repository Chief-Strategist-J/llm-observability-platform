import pytest
from pytrace_features.slow.service import SlowService
from pytrace_infra.adapters.sqlite_store import SQLiteStore

def test_slow_service_renders(capsys):
    store = SQLiteStore(":memory:")
    service = SlowService(store)
    service.monitor(200, False)
    captured = capsys.readouterr()
    assert "SLOW PATHS detected" in captured.out
    assert "epoll_wait" in captured.out

