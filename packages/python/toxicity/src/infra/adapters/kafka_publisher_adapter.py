from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from features.score_toxicity.types import ToxicityScores

class KafkaToxicityPublisherAdapter:
    def __init__(self, bootstrap_servers: str | None = None) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._producer: Any = None

    @property
    def producer(self) -> Any:
        if self._bootstrap_servers and self._producer is None:
            from confluent_kafka import Producer
            self._producer = Producer({"bootstrap.servers": self._bootstrap_servers})
        return self._producer

    def publish_flagged(
        self, trace_id: str, span_id: str, score: float, scores: ToxicityScores
    ) -> None:
        prod = self.producer
        if not prod:
            return
        payload = {
            "trace_id": trace_id,
            "span_id": span_id,
            "score": score,
            "scores": asdict(scores),
            "flag": "TOXIC_RESPONSE",
        }
        prod.produce(
            topic="llm.toxicity.flagged",
            key=trace_id,
            value=json.dumps(payload).encode("utf-8"),
        )
        prod.flush()
