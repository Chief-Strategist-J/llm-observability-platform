from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from core.config import settings

class EmbeddingService:
    def __init__(self):
        self.model: SentenceTransformer = SentenceTransformer(settings.MODEL_NAME)
    
    def embed_text(self, text: str) -> List[float]:
        embedding: np.ndarray = self.model.encode(text)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings: np.ndarray = self.model.encode(texts)
        return embeddings.tolist()
