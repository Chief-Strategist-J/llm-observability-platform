from unittest.mock import MagicMock, patch
import pytest
from worker.activities import LatencyBaselineActivities

@pytest.mark.asyncio
@patch("worker.activities.LatencyBaselineService.run_hourly_checkpoint")
async def test_latency_activities(mock_run_checkpoint: MagicMock) -> None:
    mock_run_checkpoint.return_value = 42
    
    activities = LatencyBaselineActivities(
        clickhouse=MagicMock(),
        redis=MagicMock(),
        kafka=MagicMock()
    )
    
    res = await activities.hourly_checkpoint("2026-06-23", 14)
    assert res == 42
    mock_run_checkpoint.assert_called_once()
