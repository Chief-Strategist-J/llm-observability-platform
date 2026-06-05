from __future__ import annotations

from functools import cached_property
import torch

class NliScorerAdapter:
    def __init__(self, model_id: str = "cross-encoder/nli-deberta-v3-base") -> None:
        self._model_id = model_id
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def device_name(self) -> str:
        return self._device.type

    @cached_property
    def _tokenizer(self):
        from transformers import AutoTokenizer
        return AutoTokenizer.from_pretrained(self._model_id)

    @cached_property
    def _model(self):
        from transformers import AutoModelForSequenceClassification
        model = AutoModelForSequenceClassification.from_pretrained(self._model_id)
        model = model.to(self._device)
        model.eval()
        return model

    def count_tokens(self, text: str) -> int:
        encoded = self._tokenizer(text, add_special_tokens=False)
        return len(encoded.get("input_ids", []))

    def split_context_by_tokens(self, text: str, max_tokens: int = 400) -> list[str]:
        encoded = self._tokenizer(text, add_special_tokens=False)
        input_ids = encoded.get("input_ids", [])
        if not input_ids:
            return [text]
        chunks: list[str] = []
        for i in range(0, len(input_ids), max_tokens):
            chunk_ids = input_ids[i : i + max_tokens]
            chunk_text = self._tokenizer.decode(chunk_ids, skip_special_tokens=True)
            chunks.append(chunk_text)
        return chunks

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int = 8,
    ) -> list[tuple[float, float, float]]:
        if not pairs:
            return []
        results: list[tuple[float, float, float]] = []
        for batch_start in range(0, len(pairs), batch_size):
            batch = pairs[batch_start : batch_start + batch_size]
            results.extend(self._score_batch(batch, temperature))
        return results

    def _score_batch(
        self,
        batch: list[tuple[str, str]],
        temperature: float,
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

        encoding = {k: v.to(self._device) for k, v in encoding.items()}

        with torch.no_grad():
            logits = self._model(**encoding).logits

        scaled = logits / temperature
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
