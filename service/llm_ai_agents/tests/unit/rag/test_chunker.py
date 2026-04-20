import pytest
from langchain_core.documents import Document
from services.rag.ingestion.chunker import TextChunker


def _doc(text: str) -> Document:
    return Document(page_content=text, metadata={"source": "test"})


def test_split_long_document_produces_multiple_chunks():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    long_text = "word " * 100
    chunks = chunker.split([_doc(long_text)])
    assert len(chunks) > 1


def test_split_short_document_produces_single_chunk():
    chunker = TextChunker(chunk_size=1000, chunk_overlap=0)
    chunks = chunker.split([_doc("short text")])
    assert len(chunks) == 1
    assert chunks[0].page_content == "short text"


def test_split_preserves_metadata():
    chunker = TextChunker(chunk_size=50, chunk_overlap=0)
    doc = Document(page_content="a " * 60, metadata={"source": "my-file", "page": 1})
    chunks = chunker.split([doc])
    for chunk in chunks:
        assert chunk.metadata.get("source") == "my-file"


def test_split_empty_document_returns_empty():
    chunker = TextChunker()
    chunks = chunker.split([])
    assert chunks == []


def test_chunk_overlap_causes_content_repetition():
    chunker = TextChunker(chunk_size=20, chunk_overlap=10)
    text = "abcdefghijklmnopqrstuvwxyz " * 5
    chunks = chunker.split([_doc(text)])
    assert len(chunks) >= 2
    assert len(chunks[0].page_content) <= 30


def test_multiple_documents_all_split():
    chunker = TextChunker(chunk_size=50, chunk_overlap=0)
    docs = [_doc("word " * 30), _doc("phrase " * 30)]
    chunks = chunker.split(docs)
    assert len(chunks) > 2
