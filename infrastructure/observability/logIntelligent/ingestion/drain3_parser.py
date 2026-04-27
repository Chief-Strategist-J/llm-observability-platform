from __future__ import annotations

import re
from typing import Tuple

from infrastructure.observability.logIntelligent.ingestion.template_store import TemplateStore


class Drain3LikeParser:
    _number_re = re.compile(r"\b\d+\b")
    _hex_re = re.compile(r"\b[0-9a-fA-F]{8,}\b")
    _uuid_re = re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b"
    )

    def __init__(self, template_store: TemplateStore) -> None:
        self.template_store = template_store

    def parse(self, message: str) -> Tuple[str, str]:
        template_text = self._normalize(message)
        template_id = self.template_store.register(template_text)
        return template_id, template_text

    def _normalize(self, message: str) -> str:
        normalized = self._uuid_re.sub("<UUID>", message)
        normalized = self._hex_re.sub("<HEX>", normalized)
        normalized = self._number_re.sub("<NUM>", normalized)
        return normalized
