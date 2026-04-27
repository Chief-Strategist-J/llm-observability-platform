from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional


class TraceInvertedIndex:
    def __init__(self) -> None:
        self._trace_to_lines: Dict[str, List[str]] = defaultdict(list)

    def add(self, trace_id: Optional[str], line_id: str) -> None:
        if trace_id:
            self._trace_to_lines[trace_id].append(line_id)

    def lookup(self, trace_id: str) -> List[str]:
        return list(self._trace_to_lines.get(trace_id, []))
