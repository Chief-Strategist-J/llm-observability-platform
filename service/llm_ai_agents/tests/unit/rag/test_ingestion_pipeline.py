import pytest
from langchain_core.documents import Document
from services.rag.ingestion.pipeline import IngestionPipeline
from services.shared.exceptions import RAGIngestionError
from tests.fakes.fake_document_store import FakeDocumentStore


@pytest.fixture
def store():
    return FakeDocumentStore()


@pytest.fixture
def pipeline(store):
    return IngestionPipeline(store=store, chunk_size=50, chunk_overlap=0)


def test_ingest_text_stores_chunks(pipeline, store):
    text = "word " * 50
    count = pipeline.ingest_text(text, collection="test-col")
    assert count > 0
    assert len(store.add_calls) == 1
    assert store.add_calls[0][0] == "test-col"


def test_ingest_text_returns_chunk_count(pipeline):
    text = "word " * 50
    count = pipeline.ingest_text(text, collection="col")
    assert count == len(pipeline._store.get_documents("col"))


def test_ingest_text_with_metadata(pipeline, store):
    pipeline.ingest_text("some content", collection="meta-col", metadata={"source": "api"})
    docs = store.get_documents("meta-col")
    assert all(doc.metadata.get("source") == "api" for doc in docs)


def test_ingest_url_delegates_to_loader(pipeline, store, monkeypatch):
    fake_doc = Document(page_content="web content " * 20, metadata={})
    monkeypatch.setattr(
        "services.rag.ingestion.loader.WebBaseLoader",
        lambda url: type("L", (), {"load": lambda self: [fake_doc]})(),
    )
    count = pipeline.ingest_url("http://example.com", collection="web-col")
    assert count > 0
    assert store.add_calls[0][0] == "web-col"


def test_ingest_file_real_file(pipeline, store, tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Python is great. " * 30)
    count = pipeline.ingest_file(str(f), collection="file-col")
    assert count > 0
    assert store.add_calls[0][0] == "file-col"


def test_ingest_url_wraps_error_in_rag_ingestion_error(pipeline, monkeypatch):
    monkeypatch.setattr(
        "services.rag.ingestion.loader.WebBaseLoader",
        lambda url: type("L", (), {"load": lambda self: (_ for _ in ()).throw(ConnectionError("fail"))})(),
    )
    with pytest.raises(RAGIngestionError):
        pipeline.ingest_url("http://bad.invalid", collection="err-col")
