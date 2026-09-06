from __future__ import annotations

import math
from functools import cached_property

import torch

from features.score_faithfulness.rules import NLI_BATCH_SIZE, TEMPERATURE


class DeBertaNliAdapter:
    _LABEL_ORDER = ("entailment", "neutral", "contradiction")

    def __init__(self, model_id: str = "cross-encoder/nli-deberta-v3-base") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @cached_property
    def _tokenizer(self):
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(self._model_id)

    @cached_property
    def _model(self):
        from transformers import AutoModelForSequenceClassification
        model = AutoModelForSequenceClassification.from_pretrained(self._model_id)
        model.eval()
        return model

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
    ) -> list[tuple[float, float, float]]:
        results: list[tuple[float, float, float]] = []
        for batch_start in range(0, len(pairs), NLI_BATCH_SIZE):
            batch = pairs[batch_start : batch_start + NLI_BATCH_SIZE]
            results.extend(self._score_batch(batch))
        return results

    def _score_batch(
        self,
        batch: list[tuple[str, str]],
    ) -> list[tuple[float, float, float]]:
        premises = [p for p, _ in batch]
        hypotheses = [h for _, h in batch]

        encoding = self._tokenizer(
            premises,
            hypotheses,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512,
        )

        with torch.no_grad():
            logits = self._model(**encoding).logits

        scaled = logits / TEMPERATURE
        probs = torch.softmax(scaled, dim=-1).tolist()

        label_to_idx = {
            label: idx
            for idx, label in enumerate(self._model.config.id2label.values())
        }

        e_idx = label_to_idx.get("entailment", 0)
        n_idx = label_to_idx.get("neutral", 1)
        c_idx = label_to_idx.get("contradiction", 2)

        return [
            (row[e_idx], row[n_idx], row[c_idx])
            for row in probs
        ]
