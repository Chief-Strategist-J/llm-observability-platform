from sentence_transformers import SentenceTransformer
from typing import List
from core.ports.embedding_model import EmbeddingModelPort
import asyncio

class SentenceTransformerEmbedding(EmbeddingModelPort):
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
    
    async def embed_text(self, text: str) -> List[float]:
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, self.model.encode, text
        )
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.model.encode, texts
        )
        return [emb.tolist() for emb in embeddings]
    
    def get_dimension(self) -> int:
        return self.dimension
