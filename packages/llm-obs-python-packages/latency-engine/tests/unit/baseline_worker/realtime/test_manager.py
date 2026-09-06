import pytest
from unittest.mock import AsyncMock, MagicMock
from realtime.connection.manager import ConnectionManager
from realtime.connection.types import ConnectionState
from realtime.sse.types import SSEEvent

@pytest.mark.asyncio
async def test_connection_manager_lifecycle() -> None:
    client = MagicMock()
    client.connect.return_value = True
    
    manager = ConnectionManager(client=client)
    assert manager.state == ConnectionState.CLOSED
    
    connected = await manager.connect("http://fake")
    assert connected is True
    assert manager.state == ConnectionState.CONNECTED
    client.connect.assert_called_once_with("http://fake")
    
    manager.disconnect()
    assert manager.state == ConnectionState.CLOSED
    client.disconnect.assert_called_once()
