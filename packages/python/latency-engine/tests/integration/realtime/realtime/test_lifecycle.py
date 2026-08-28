import pytest
from unittest.mock import AsyncMock, MagicMock
from realtime.connection.manager import ConnectionManager
from realtime.connection.types import ConnectionState
from realtime.retry.policy import RetryPolicy
from realtime.retry.types import RetryConfig

@pytest.mark.asyncio
async def test_lifecycle_integration() -> None:
    # Set up client that fails twice then succeeds
    client = MagicMock()
    client.connect.side_effect = [False, False, True]
    
    config = RetryConfig(max_attempts=3, initial_delay=0.001, jitter=False)
    policy = RetryPolicy(config)
    manager = ConnectionManager(client=client, policy=policy)
    
    # Trigger connection which will trigger reconnect loop
    connected = await manager.connect("http://fake")
    assert connected is True
    assert manager.state == ConnectionState.CONNECTED
    assert client.connect.call_count == 3
    
    # Disconnect
    manager.disconnect()
    assert manager.state == ConnectionState.CLOSED
