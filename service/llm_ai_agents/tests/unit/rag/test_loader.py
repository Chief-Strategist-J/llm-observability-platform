import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from services.rag.ingestion.loader import DocumentLoader


@pytest.fixture
def loader():
    return DocumentLoader()


def test_from_text_returns_one_document(loader):
    docs = loader.from_text("hello world")
    assert len(docs) == 1
    assert docs[0].page_content == "hello world"


def test_from_text_attaches_metadata(loader):
    docs = loader.from_text("content", metadata={"source": "api", "page": 1})
    assert docs[0].metadata["source"] == "api"
    assert docs[0].metadata["page"] == 1


def test_from_text_empty_metadata_defaults_to_empty_dict(loader):
    docs = loader.from_text("text")
    assert docs[0].metadata == {}


def test_from_url_delegates_to_web_base_loader(loader):
    fake_doc = Document(page_content="web content", metadata={"source": "http://example.com"})
    with patch("services.rag.ingestion.loader.WebBaseLoader") as MockLoader:
        MockLoader.return_value.load.return_value = [fake_doc]
        docs = loader.from_url("http://example.com")
        MockLoader.assert_called_once_with("http://example.com")
        assert docs[0].page_content == "web content"


def test_from_file_delegates_to_text_loader(loader, tmp_path):
    test_file = tmp_path / "doc.txt"
    test_file.write_text("file content here")
    docs = loader.from_file(str(test_file))
    assert any("file content here" in doc.page_content for doc in docs)


def test_from_url_propagates_loader_error(loader):
    with patch("services.rag.ingestion.loader.WebBaseLoader") as MockLoader:
        MockLoader.return_value.load.side_effect = ConnectionError("network unreachable")
        with pytest.raises(ConnectionError):
            loader.from_url("http://bad-url.invalid")
