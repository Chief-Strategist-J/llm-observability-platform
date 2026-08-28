from unittest.mock import patch, MagicMock
from realtime.sse.client import SSEClient
from realtime.sse.types import SSEEvent
from realtime.sse.last_event_id import LastEventIdStore

@patch("urllib.request.urlopen")
def test_client_connect(mock_urlopen) -> None:
    mock_conn = MagicMock()
    mock_urlopen.return_value = mock_conn
    
    store = LastEventIdStore(filepath="/tmp/non_existent.txt")
    client = SSEClient(last_event_id_store=store)
    
    assert client.connect("http://fake-sse-server/stream") is True
    assert client.connected is True
    
    client.disconnect()
    assert client.connected is False
    mock_conn.close.assert_called_once()

@patch("urllib.request.urlopen")
def test_client_send_event_carries_attempt_span_attributes(mock_urlopen) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"status": "ok", "id": "event-999"}'
    mock_urlopen.return_value.__enter__.return_value = mock_response
    
    store = MagicMock()
    client = SSEClient(last_event_id_store=store)
    
    event = SSEEvent(
        event_type="checkpoint_created",
        data={"checkpoint_id": 1},
        workflow_id="wf-1",
        run_id="run-1",
        attempt=2
    )
    
    # Send event
    with patch("realtime.sse.client.trace_span") as mock_trace_span:
        mock_span = MagicMock()
        mock_trace_span.return_value.__enter__.return_value = mock_span
        
        success = client.send_event("http://fake-sse-server/events", event)
        
        assert success is True
        # Assert attempt is carried as span attribute (from rule: "Activity attempt number is carried as a span attribute into every SSE event")
        mock_span.set_attribute.assert_any_call("attempt", 2)
        mock_span.set_attribute.assert_any_call("workflow_id", "wf-1")
        mock_span.set_attribute.assert_any_call("run_id", "run-1")
        
        # Verify Last-Event-ID updated
        store.save.assert_called_with("event-999")
