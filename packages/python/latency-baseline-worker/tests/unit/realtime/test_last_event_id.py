import os
from realtime.sse.last_event_id import LastEventIdStore

def test_last_event_id_store_workflow(tmp_path) -> None:
    filepath = str(tmp_path / "last_id.txt")
    store = LastEventIdStore(filepath=filepath)
    
    # Empty
    assert store.get() is None
    
    # Save
    store.save("event-123")
    assert store.get() == "event-123"
    
    # Inject
    headers = {}
    headers = store.inject_header(headers)
    assert headers["Last-Event-ID"] == "event-123"
