from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch
import pytest

from features.score_toxicity.types import ToxicityScores
from infra.adapters.kafka_publisher_adapter import KafkaToxicityPublisherAdapter

def test_producer_not_initialized_without_bootstrap():
    adapter = KafkaToxicityPublisherAdapter(bootstrap_servers=None)
    assert adapter.producer is None

def test_producer_initialized_with_bootstrap():
    mock_producer_class = MagicMock()
    with patch.dict(sys.modules, {"confluent_kafka": MagicMock()}):
        import confluent_kafka
        confluent_kafka.Producer = mock_producer_class
        adapter = KafkaToxicityPublisherAdapter(bootstrap_servers="localhost:9092")
        assert adapter.producer is not None
        mock_producer_class.assert_called_once_with({"bootstrap.servers": "localhost:9092"})

def test_publish_flagged():
    mock_producer = MagicMock()
    adapter = KafkaToxicityPublisherAdapter(bootstrap_servers="localhost:9092")
    adapter._producer = mock_producer

    scores = ToxicityScores(0.8, 0.1, 0.2, 0.3, 0.4, 0.5)
    adapter.publish_flagged("trace123", "span456", 0.8, scores)

    mock_producer.produce.assert_called_once()
    mock_producer.flush.assert_called_once()
    call_args = mock_producer.produce.call_args[1]
    assert call_args["topic"] == "llm.toxicity.flagged"
    assert call_args["key"] == "trace123"
    assert b"trace123" in call_args["value"]
