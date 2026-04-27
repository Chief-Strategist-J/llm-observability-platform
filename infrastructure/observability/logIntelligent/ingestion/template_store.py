from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    template_id: Optional[str] = None


class TemplateStore:
    def __init__(self) -> None:
        self._template_by_id: Dict[str, str] = {}
        self._root = TrieNode()

    def register(self, template_text: str) -> str:
        template_id = hashlib.sha1(template_text.encode("utf-8")).hexdigest()[:16]
        self._template_by_id[template_id] = template_text
        self._insert(template_text, template_id)
        return template_id

    def get(self, template_id: str) -> Optional[str]:
        return self._template_by_id.get(template_id)

    def find_template_id(self, template_text: str) -> Optional[str]:
        node = self._root
        for token in template_text.split():
            if token not in node.children:
                return None
            node = node.children[token]
        return node.template_id

    def _insert(self, template_text: str, template_id: str) -> None:
        node = self._root
        for token in template_text.split():
            node = node.children.setdefault(token, TrieNode())
        node.template_id = template_id
