from typing import List
from langchain_core.documents import Document
from services.rag.ports.retriever import RetrieverPort


class GraphSearchRetriever(RetrieverPort):
    def retrieve(self, query: str, collection: str, k: int = 4) -> List[Document]:
        raise NotImplementedError("Graph RAG retrieval is not yet implemented")
