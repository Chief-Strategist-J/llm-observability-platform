from __future__ import annotations

from unittest.mock import MagicMock
import pytest

from features.latency_query.repository import LatencyQueryRepository
from features.latency_query.service import LatencyQueryService
from shared.errors.latency_query_errors import AttributionNotFoundError


def test_service_get_attribution_success():
    # Arrange
    mock_redis = MagicMock()
    mock_clickhouse = MagicMock()
    
    mock_redis.get_attribution_avg.return_value = {
        "dns": 10.0,
        "tcp": 20.0,
        "queue": 50.0,
        "inference": 700.0,
    }
    
    repo = LatencyQueryRepository(redis=mock_redis, clickhouse=mock_clickhouse)
    service = LatencyQueryService(repository=repo, slo_thresholds={})

    # Act
    res = service.get_attribution("gpt-4", "2026061708")

    # Assert
    assert res.dns == 10.0
    assert res.tcp == 20.0
    assert res.queue == 50.0
    assert res.inference == 700.0
    mock_redis.get_attribution_avg.assert_called_once_with("gpt-4", "2026061708")


def test_service_get_attribution_not_found():
    # Arrange
    mock_redis = MagicMock()
    mock_clickhouse = MagicMock()
    
    mock_redis.get_attribution_avg.return_value = None
    
    repo = LatencyQueryRepository(redis=mock_redis, clickhouse=mock_clickhouse)
    service = LatencyQueryService(repository=repo, slo_thresholds={})

    # Act & Assert
    with pytest.raises(AttributionNotFoundError):
        service.get_attribution("gpt-4", "2026061708")
