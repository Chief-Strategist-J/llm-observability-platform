from __future__ import annotations

import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, Tuple


LOG_LEVEL_MAP = {
    "warn": "WARNING",
    "warning": "WARNING",
    "err": "ERROR",
    "error": "ERROR",
    "info": "INFO",
    "debug": "DEBUG",
    "trace": "TRACE",
    "fatal": "FATAL",
}


class StructuralEnricher:
    _timestamp_re = re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?")
    _trace_id_re = re.compile(r"\b(?:trace[_-]?id|tid)=([A-Za-z0-9\-]+)", re.IGNORECASE)
    _service_re = re.compile(r"\bservice=([A-Za-z0-9._-]+)", re.IGNORECASE)
    _level_re = re.compile(r"\b(INFO|WARN|WARNING|ERROR|DEBUG|TRACE|FATAL|ERR)\b", re.IGNORECASE)

    def __init__(self) -> None:
        self._cardinality: Dict[str, Counter] = defaultdict(Counter)

    def enrich(self, message: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, int]]:
        extracted: Dict[str, str] = {}

        timestamp = self._timestamp_re.search(message)
        if timestamp:
            extracted["timestamp"] = timestamp.group(0)

        level = self._level_re.search(message)
        if level:
            extracted["level"] = level.group(1)

        service = self._service_re.search(message)
        if service:
            extracted["service"] = service.group(1)

        trace_id = self._trace_id_re.search(message)
        if trace_id:
            extracted["trace_id"] = trace_id.group(1)

        normalized = self._normalize(extracted)
        cardinality = self._update_cardinality(normalized)
        return extracted, normalized, cardinality

    def _normalize(self, extracted: Dict[str, str]) -> Dict[str, str]:
        normalized: Dict[str, str] = dict(extracted)

        timestamp = extracted.get("timestamp")
        if timestamp:
            try:
                parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                normalized["timestamp"] = parsed.astimezone(timezone.utc).isoformat()
            except ValueError:
                normalized["timestamp"] = timestamp

        level = extracted.get("level")
        if level:
            normalized["level"] = LOG_LEVEL_MAP.get(level.lower(), level.upper())

        if "service" not in normalized:
            normalized["service"] = "unknown"

        return normalized

    def _update_cardinality(self, normalized: Dict[str, str]) -> Dict[str, int]:
        snapshot: Dict[str, int] = {}
        for field_name, value in normalized.items():
            self._cardinality[field_name][value] += 1
            snapshot[field_name] = len(self._cardinality[field_name])
        return snapshot
