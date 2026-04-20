from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class DocumentStorePort(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document], collection: str) -> None:
        pass

    @abstractmethod
    def delete_collection(self, collection: str) -> None:
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        pass
