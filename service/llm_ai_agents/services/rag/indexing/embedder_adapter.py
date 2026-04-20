from typing import List
from langchain_community.embeddings import SentenceTransformerEmbeddings
from services.rag.ports.embedder import EmbedderPort


class SentenceTransformerEmbedder(EmbedderPort):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self._model = SentenceTransformerEmbeddings(model_name=model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._model.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        return self._model.embed_query(text)

    def as_langchain_embeddings(self):
        return self._model
