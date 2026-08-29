from __future__ import annotations

import json
import logging
from typing import Any, Callable
from confluent_kafka import Producer, KafkaError

logger = logging.getLogger(__name__)


class KafkaProducerClient:
    def __init__(self, producer: Producer) -> None:
        self._producer = producer

    def produce(
        self,
        topic: str,
        value: dict[str, Any] | str | bytes,
        key: str | bytes | None = None,
        headers: dict[str, str | bytes] | list[tuple[str, str | bytes]] | None = None,
        on_delivery: Callable[[KafkaError | None, Any], None] | None = None,
    ) -> None:
        if isinstance(value, dict):
            payload = json.dumps(value).encode("utf-8")
        elif isinstance(value, str):
            payload = value.encode("utf-8")
        else:
            payload = value

        header_list: list[tuple[str, bytes]] | None = None
        if isinstance(headers, dict):
            header_list = [
                (k, v.encode("utf-8") if isinstance(v, str) else v)
                for k, v in headers.items()
            ]
        elif isinstance(headers, list):
            header_list = [
                (k, v.encode("utf-8") if isinstance(v, str) else v)
                for k, v in headers
            ]

        def _delivery_cb(err: KafkaError | None, msg: Any) -> None:
            if err is not None:
                logger.error("Kafka produce failed to topic %s: %s", topic, err)
            if on_delivery:
                on_delivery(err, msg)

        self._producer.produce(
            topic=topic,
            value=payload,
            key=key,
            headers=header_list,
            callback=_delivery_cb,
        )
        self._producer.poll(0)

    def flush(self, timeout: float = 10.0) -> int:
        return self._producer.flush(timeout)
