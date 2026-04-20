from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document


class RetrieverPort(ABC):
    @abstractmethod
    def retrieve(self, query: str, collection: str, k: int = 4) -> List[Document]:
        pass
