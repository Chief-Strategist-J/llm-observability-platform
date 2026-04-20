from typing import Dict, List
from langchain_core.documents import Document
from services.rag.ports.retriever import RetrieverPort
from services.rag.ports.document_store import DocumentStorePort


class FakeRetriever(RetrieverPort, DocumentStorePort):
    def __init__(self, documents: List[Document] = None):
        self._docs: Dict[str, List[Document]] = {}
        self._preset: List[Document] = documents or []
        self.retrieve_calls: List[tuple] = []
        self.add_calls: List[tuple] = []
        self.delete_calls: List[str] = []

    def retrieve(self, query: str, collection: str, k: int = 4) -> List[Document]:
        self.retrieve_calls.append((query, collection, k))
        stored = self._docs.get(collection, self._preset)
        return stored[:k]

    def add_documents(self, documents: List[Document], collection: str) -> None:
        self.add_calls.append((collection, len(documents)))
        if collection not in self._docs:
            self._docs[collection] = []
        self._docs[collection].extend(documents)

    def delete_collection(self, collection: str) -> None:
        self.delete_calls.append(collection)
        self._docs.pop(collection, None)

    def list_collections(self) -> List[str]:
        return list(self._docs.keys())
