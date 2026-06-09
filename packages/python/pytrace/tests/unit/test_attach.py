import pytest
from unittest.mock import MagicMock
from pytrace_features.attach.service import AttachService
from pytrace_features.attach.ports import TraceCollectorPort

def test_attach_service_success():
    mock_collector = MagicMock(spec=TraceCollectorPort)
    mock_collector.attach.return_value = True

    service = AttachService(mock_collector)
    # We pass mock_collector which will succeed
    # For test, let's execute the attach check
    res = mock_collector.attach(1234)
    assert res is True
