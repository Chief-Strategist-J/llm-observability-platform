import logging
from realtime.connection.types import ConnectionState
from realtime.connection.state import ConnectionStateTracker
from realtime.sse.client import SSEClient
from realtime.sse.reconnect import ReconnectLoop
from realtime.sse.types import SSEEvent
from realtime.retry.policy import RetryPolicy

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, client: SSEClient | None = None, policy: RetryPolicy | None = None) -> None:
        self.client = client or SSEClient()
        self.state_tracker = ConnectionStateTracker()
        self.policy = policy or RetryPolicy()
        self.reconnect_loop = ReconnectLoop(self.policy)

    @property
    def state(self) -> ConnectionState:
        return self.state_tracker.value

    async def connect(self, url: str) -> bool:
        """Manage connection lifecycle, updating state accordingly."""
        if self.state == ConnectionState.CONNECTED:
            return True

        self.state_tracker._set_state(ConnectionState.CONNECTING)
        
        async def _connect_callback() -> bool:
            return self.client.connect(url)

        success = await self.reconnect_loop.execute(_connect_callback)
        if success:
            self.state_tracker._set_state(ConnectionState.CONNECTED)
            return True
        else:
            self.state_tracker._set_state(ConnectionState.CLOSED)
            return False

    def disconnect(self) -> None:
        """Disconnect the client and close state."""
        self.client.disconnect()
        self.state_tracker._set_state(ConnectionState.CLOSED)

    def send_event(self, url: str, event: SSEEvent) -> bool:
        """Send event via client. Only manager calls client."""
        return self.client.send_event(url, event)
