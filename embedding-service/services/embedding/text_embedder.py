"""Text embedding service."""
import hashlib
from typing import List
import logging

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self, model_name: str = "demo", vector_dim: int = 384):
        self.model_name = model_name
        self.vector_dim = vector_dim
        self._load_model()
    
    def _load_model(self):
        """Load embedding model."""
        if self.model_name == "demo":
            logger.info("Using demo hash-based embedder")
        else:
            try:
                # Uncomment for production:
                # from sentence_transformers import SentenceTransformer
                # self.model = SentenceTransformer(self.model_name)
                pass
            except ImportError:
                logger.warning("sentence-transformers not available, using demo embedder")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.model_name == "demo":
            return self._hash_embed(text)
        else:
            # return self.model.encode(text).tolist()
            return self._hash_embed(text)
    
    def _hash_embed(self, text: str) -> List[float]:
        """Demo embedding using hash."""
        if not text:
            text = "empty"
        
        # Create deterministic hash
        hash_bytes = hashlib.sha256(text.lower().encode()).digest()
        
        # Convert to vector
        vector = []
        for i in range(self.vector_dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            # Normalize to [-1, 1]
            normalized = (byte_val - 127.5) / 127.5
            vector.append(float(normalized))
        
        return vector
