from realtime.connection.state import ConnectionStateTracker
from realtime.connection.types import ConnectionState

def test_connection_state_tracker_readonly() -> None:
    tracker = ConnectionStateTracker()
    assert tracker.value == ConnectionState.CLOSED
    
    tracker._set_state(ConnectionState.CONNECTING)
    assert tracker.value == ConnectionState.CONNECTING
