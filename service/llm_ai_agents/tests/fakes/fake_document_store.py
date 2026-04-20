from typing import Dict, List
from langchain_core.documents import Document
from services.rag.ports.document_store import DocumentStorePort


class FakeDocumentStore(DocumentStorePort):
    def __init__(self):
        self._collections: Dict[str, List[Document]] = {}
        self.add_calls: List[tuple] = []
        self.delete_calls: List[str] = []

    def add_documents(self, documents: List[Document], collection: str) -> None:
        self.add_calls.append((collection, len(documents)))
        if collection not in self._collections:
            self._collections[collection] = []
        self._collections[collection].extend(documents)

    def delete_collection(self, collection: str) -> None:
        self.delete_calls.append(collection)
        self._collections.pop(collection, None)

    def list_collections(self) -> List[str]:
        return list(self._collections.keys())

    def get_documents(self, collection: str) -> List[Document]:
        return self._collections.get(collection, [])
