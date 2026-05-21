import hashlib
import uuid
from typing import Any
from ...ports import SamplingGatePort

class Sha256SamplingAdapter(SamplingGatePort):
    def should_sample(self, span_id: Any) -> bool:
        if isinstance(span_id, uuid.UUID):
            span_id_bytes = span_id.bytes
        elif isinstance(span_id, str):
            try:
                span_id_bytes = uuid.UUID(span_id).bytes
            except ValueError:
                span_id_bytes = span_id.encode("utf-8")
        elif isinstance(span_id, bytes):
            span_id_bytes = span_id
        else:
            span_id_bytes = str(span_id).encode("utf-8")
        h = hashlib.sha256(span_id_bytes).digest()
        val = int.from_bytes(h, byteorder="big")
        return (val % 100) == 0
