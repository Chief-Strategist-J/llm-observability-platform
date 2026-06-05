import os
import threading
from functools import cached_property
import torch

class NliScorerAdapter:
    def __init__(self, model_id: str = "cross-encoder/nli-deberta-v3-base") -> None:
        self._model_id = model_id
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._lock = threading.Lock()
        self._batch_size = int(os.getenv("NLI_BATCH_SIZE", "8"))

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
        batch_size: int | None = None,
    ) -> list[tuple[float, float, float]]:
        if not pairs:
            return []
        bs = batch_size or self._batch_size
        results: list[tuple[float, float, float]] = []
        for batch_start in range(0, len(pairs), bs):
            batch = pairs[batch_start : batch_start + bs]
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
            truncation="only_first",
            padding=True,
            max_length=512,
        )

        encoding = {k: v.to(self._device) for k, v in encoding.items()}

        with self._lock:
            with torch.no_grad():
                logits = self._model(**encoding).logits

        scaled = logits / temperature
        probs = torch.softmax(scaled, dim=-1).tolist()

        id2label = getattr(self._model.config, "id2label", {}) or {}
        label_to_idx = {
            str(label).lower(): int(idx)
            for idx, label in id2label.items()
        }

        # True DeBERTa NLI logit order: 0 = contradiction, 1 = entailment, 2 = neutral
        c_idx = label_to_idx.get("contradiction", 0)
        e_idx = label_to_idx.get("entailment", 1)
        n_idx = label_to_idx.get("neutral", 2)

        return [
            (row[e_idx], row[n_idx], row[c_idx])
            for row in probs
        ]
