import os
import threading
import torch

class NliScorerAdapter:
    def __init__(self, default_model_id: str = "cross-encoder/nli-deberta-v3-base") -> None:
        self._default_model_id = default_model_id
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._lock = threading.Lock()
        self._batch_size = int(os.getenv("NLI_BATCH_SIZE", "8"))
        self._models: dict[str, torch.nn.Module] = {}
        self._tokenizers: dict[str, any] = {}

    @property
    def default_model_id(self) -> str:
        return self._default_model_id

    @property
    def device_name(self) -> str:
        return self._device.type

    def _get_model_and_tokenizer(self, model_id: str | None = None) -> tuple[any, any]:
        m_id = model_id or self._default_model_id
        with self._lock:
            if m_id not in self._models:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                tokenizer = AutoTokenizer.from_pretrained(m_id)
                model = AutoModelForSequenceClassification.from_pretrained(m_id)
                model = model.to(self._device)
                model.eval()
                self._models[m_id] = model
                self._tokenizers[m_id] = tokenizer
            return self._models[m_id], self._tokenizers[m_id]

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        _, tokenizer = self._get_model_and_tokenizer(model_id)
        encoded = tokenizer(text, add_special_tokens=False)
        return len(encoded.get("input_ids", []))

    def split_context_by_tokens(
        self,
        text: str,
        max_tokens: int = 400,
        model_id: str | None = None,
    ) -> list[str]:
        _, tokenizer = self._get_model_and_tokenizer(model_id)
        encoded = tokenizer(text, add_special_tokens=False)
        input_ids = encoded.get("input_ids", [])
        if not input_ids:
            return [text]
        chunks: list[str] = []
        for i in range(0, len(input_ids), max_tokens):
            chunk_ids = input_ids[i : i + max_tokens]
            chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True)
            chunks.append(chunk_text)
        return chunks

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int | None = None,
        model_id: str | None = None,
    ) -> list[tuple[float, float, float]]:
        if not pairs:
            return []
        bs = batch_size or self._batch_size
        results: list[tuple[float, float, float]] = []
        for batch_start in range(0, len(pairs), bs):
            batch = pairs[batch_start : batch_start + bs]
            results.extend(self._score_batch(batch, temperature, model_id))
        return results

    def _score_batch(
        self,
        batch: list[tuple[str, str]],
        temperature: float,
        model_id: str | None = None,
    ) -> list[tuple[float, float, float]]:
        premises = [p for p, _ in batch]
        hypotheses = [h for _, h in batch]

        model, tokenizer = self._get_model_and_tokenizer(model_id)

        encoding = tokenizer(
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
                logits = model(**encoding).logits

        scaled = logits / temperature
        probs = torch.softmax(scaled, dim=-1).tolist()

        id2label = getattr(model.config, "id2label", {}) or {}
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
