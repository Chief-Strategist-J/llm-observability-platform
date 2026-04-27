from __future__ import annotations

from collections import defaultdict, deque
from typing import Deque, Dict


class ADWINLikeDriftDetector:
    def __init__(self, max_window: int = 50, sensitivity: float = 0.35) -> None:
        self.max_window = max_window
        self.sensitivity = sensitivity
        self._windows: Dict[str, Deque[int]] = defaultdict(lambda: deque(maxlen=max_window))

    def update(self, template_id: str, count: int) -> bool:
        window = self._windows[template_id]
        window.append(count)
        if len(window) < max(10, self.max_window // 2):
            return False

        half = len(window) // 2
        first = list(window)[:half]
        second = list(window)[half:]
        if not first or not second:
            return False

        first_mean = sum(first) / len(first)
        second_mean = sum(second) / len(second)
        baseline = max(first_mean, 1.0)
        return abs(second_mean - first_mean) / baseline >= self.sensitivity
