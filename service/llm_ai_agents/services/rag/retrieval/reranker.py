from typing import List, Tuple
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: List[Document], top_k: int = 3) -> List[Document]:
        if not documents:
            return documents
        pairs = [(query, doc.page_content) for doc in documents]
        scores = self._model.predict(pairs)
        scored = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
