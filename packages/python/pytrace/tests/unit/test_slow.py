import pytest
from pytrace_features.slow.service import SlowService

def test_slow_service_renders(capsys):
    service = SlowService()
    service.monitor(200, False)
    captured = capsys.readouterr()
    assert "SLOW PATHS detected" in captured.out
    assert "epoll_wait" in captured.out
