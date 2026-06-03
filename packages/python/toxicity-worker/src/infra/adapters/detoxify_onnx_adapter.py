from __future__ import annotations

from functools import cached_property
from typing import Any
import torch

from core.domain.ports.toxicity_scorer_port import ToxicityScorerPort
from core.domain.types import ToxicityScores

class DetoxifyOnnxAdapter(ToxicityScorerPort):
    def __init__(self, model_id: str = "unitary/toxic-bert") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @cached_property
    def _tokenizer(self) -> Any:
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(self._model_id)

    @cached_property
    def _model(self) -> Any:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        return ORTModelForSequenceClassification.from_pretrained(self._model_id, export=True)

    def tokenize(self, text: str) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def score_token_ids(self, token_ids: list[int]) -> ToxicityScores:
        cls_id = self._tokenizer.cls_token_id or 101
        sep_id = self._tokenizer.sep_token_id or 102
        full_ids = [cls_id] + token_ids + [sep_id]
        attention_mask = [1] * len(full_ids)

        inputs = {
            "input_ids": torch.tensor([full_ids]),
            "attention_mask": torch.tensor([attention_mask]),
        }

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.sigmoid(outputs.logits)[0].tolist()

        id2label = self._model.config.id2label
        label_to_idx = {name.lower(): idx for idx, name in id2label.items()}

        return ToxicityScores(
            toxicity=probs[label_to_idx.get("toxicity", 0)],
            severe_toxicity=probs[label_to_idx.get("severe_toxicity", 1)],
            obscene=probs[label_to_idx.get("obscene", 2)],
            threat=probs[label_to_idx.get("threat", 3)],
            insult=probs[label_to_idx.get("insult", 4)],
            identity_hate=probs[label_to_idx.get("identity_hate", 5)],
        )
