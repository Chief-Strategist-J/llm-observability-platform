import asyncio
from unittest.mock import Mock, AsyncMock
from kafka_messaging_internal.features.event_processing.service import EventProcessingService

async def test():
    mock_db = Mock()
    mock_db.get_events_by_topic = AsyncMock(return_value=[])
    
    # Simulate test
    mock_event = Mock()
    mock_db.get_events_by_topic.return_value = [mock_event]
    
    service = EventProcessingService(mock_db)
    
    res = await service.query_events({"topic": "test", "limit": 10, "offset": 0})
    print(res)

asyncio.run(test())
