from typing import List
import asyncio
from sentence_transformers import SentenceTransformer
from core.ports.embedding_model import EmbeddingModelPort

class SentenceTransformerModel(EmbeddingModelPort):
    _instance = None
    _model = None

    def __new__(cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._model = SentenceTransformer(model_name)
        return cls._instance

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, show_progress_bar=False, normalize_embeddings=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, show_progress_bar=False, batch_size=8, normalize_embeddings=True)
        )
        return [emb.tolist() for emb in embeddings]
