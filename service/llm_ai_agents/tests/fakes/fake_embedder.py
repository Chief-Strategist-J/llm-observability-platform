from typing import List
from services.rag.ports.embedder import EmbedderPort


class FakeEmbedder(EmbedderPort):
    def __init__(self, dim: int = 4):
        self._dim = dim
        self.embed_document_calls: List[List[str]] = []
        self.embed_query_calls: List[str] = []

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self.embed_document_calls.append(texts)
        return [[float(i % self._dim)] * self._dim for i in range(len(texts))]

    def embed_query(self, text: str) -> List[float]:
        self.embed_query_calls.append(text)
        return [0.5] * self._dim
