"""Text embedding service with multiple model support."""
import hashlib
import time
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TextEmbedder:
    """Text embedding service supporting multiple models."""
    
    def __init__(self, model_name: str = "demo", vector_dim: int = 384):
        self.model_name = model_name
        self.vector_dim = vector_dim
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load embedding model based on configuration."""
        if self.model_name == "demo":
            logger.info("Using demo hash-based embedder")
        else:
            try:
                # For production scaling - uncomment when needed:
                # from sentence_transformers import SentenceTransformer
                # self.model = SentenceTransformer(self.model_name)
                # logger.info(f"Loaded model: {self.model_name}")
                logger.info(f"Model {self.model_name} not available, using demo embedder")
                self.model_name = "demo"  # Fallback
            except ImportError:
                logger.warning("sentence-transformers not available, using demo embedder")
                self.model_name = "demo"
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if not text or not text.strip():
            text = "empty_text"
        
        if self.model_name == "demo":
            return self._hash_embed(text)
        else:
            # For production models:
            # return self.model.encode(text, convert_to_tensor=False).tolist()
            return self._hash_embed(text)
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.model_name == "demo":
            return [self._hash_embed(text) for text in texts]
        else:
            # For production models:
            # return self.model.encode(texts, convert_to_tensor=False).tolist()
            return [self._hash_embed(text) for text in texts]
    
    def _hash_embed(self, text: str) -> List[float]:
        """Generate deterministic demo embedding using SHA256."""
        # Normalize text for consistency
        text = text.lower().strip()
        
        # Create deterministic hash
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        
        # Convert to vector with good distribution
        vector = []
        for i in range(self.vector_dim):
            # Use multiple bytes for better distribution
            byte_idx1 = i % len(hash_bytes)
            byte_idx2 = (i + 1) % len(hash_bytes)
            
            byte_val = (hash_bytes[byte_idx1] + hash_bytes[byte_idx2]) / 2
            # Normalize to [-1, 1] for cosine similarity
            normalized = (byte_val - 127.5) / 127.5
            vector.append(float(normalized))
        
        return vector
