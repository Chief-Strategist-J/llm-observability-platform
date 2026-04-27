from __future__ import annotations

from collections import deque
from typing import Deque, List

from sklearn.ensemble import IsolationForest


class IsolationForestLikeScorer:
    def __init__(self, window_size: int = 256, retrain_interval: int = 32) -> None:
        self.window_size = window_size
        self.retrain_interval = retrain_interval
        self._samples: Deque[List[float]] = deque(maxlen=window_size)
        self._model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        self._updates = 0
        self._trained = False

    def score(self, template_count: int, unseen_fields: int, drift_detected: bool) -> float:
        sample = [float(template_count), float(unseen_fields), 1.0 if drift_detected else 0.0]
        self._samples.append(sample)
        self._updates += 1

        if len(self._samples) >= 32 and (not self._trained or self._updates % self.retrain_interval == 0):
            self._model.fit(list(self._samples))
            self._trained = True

        if not self._trained:
            rarity = 1.0 / max(template_count, 1)
            field_component = min(unseen_fields / 10.0, 1.0)
            drift_component = 0.4 if drift_detected else 0.0
            return min(1.0, (0.5 * rarity) + (0.3 * field_component) + drift_component)

        decision = float(self._model.decision_function([sample])[0])
        scaled = 1.0 / (1.0 + pow(2.718281828, decision * 3.0))
        return max(0.0, min(1.0, scaled))
