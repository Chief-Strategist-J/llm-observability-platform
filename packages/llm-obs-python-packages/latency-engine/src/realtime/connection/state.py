from realtime.connection.types import ConnectionState

class ConnectionStateTracker:
    def __init__(self) -> None:
        self._state = ConnectionState.CLOSED

    @property
    def value(self) -> ConnectionState:
        return self._state

    def _set_state(self, new_state: ConnectionState) -> None:
        """Internal setter, should only be called by the ConnectionManager."""
        self._state = new_state
