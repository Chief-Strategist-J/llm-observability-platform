import pytest
from unittest.mock import MagicMock
from realtime.connection.manager import ConnectionManager
from realtime.connection.types import ConnectionState
from realtime.retry.policy import RetryPolicy
from realtime.retry.types import RetryConfig

@pytest.mark.asyncio
async def test_retry_exhaust_integration() -> None:
    client = MagicMock()
    client.connect.return_value = False
    
    config = RetryConfig(max_attempts=3, initial_delay=0.001, jitter=False)
    policy = RetryPolicy(config)
    manager = ConnectionManager(client=client, policy=policy)
    
    connected = await manager.connect("http://fake")
    assert connected is False
    assert manager.state == ConnectionState.CLOSED
    assert client.connect.call_count == 3
