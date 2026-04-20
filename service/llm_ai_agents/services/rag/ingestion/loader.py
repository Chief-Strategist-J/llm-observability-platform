from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import WebBaseLoader, TextLoader
from langchain_core.documents import Document as LCDocument


class DocumentLoader:
    def from_url(self, url: str) -> List[Document]:
        return WebBaseLoader(url).load()

    def from_file(self, file_path: str) -> List[Document]:
        return TextLoader(file_path).load()

    def from_text(self, text: str, metadata: dict = None) -> List[Document]:
        return [LCDocument(page_content=text, metadata=metadata or {})]
