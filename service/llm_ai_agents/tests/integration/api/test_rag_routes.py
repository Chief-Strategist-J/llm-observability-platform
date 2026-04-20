import pytest
from unittest.mock import patch, MagicMock

def test_rag_ingest_success(client):
    with patch("services.api.routes.rag.get_rag_service") as mock_service_factory:
        mock_service = MagicMock()
        mock_service.ingest.return_value = 10
        mock_service_factory.return_value = mock_service
        
        response = client.post("/api/rag/ingest", json={
            "source": "Some text content",
            "source_type": "text",
            "collection": "test-col"
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["chunks_indexed"] == 10
        assert data["collection"] == "test-col"

def test_rag_query_success(client):
    with patch("services.api.routes.rag.get_rag_service") as mock_service_factory:
        mock_service = MagicMock()
        mock_service.query.return_value = {
            "answer": "RAG answer",
            "sources": [],
            "chunks_retrieved": 3
        }
        mock_service_factory.return_value = mock_service
        
        with patch("services.api.routes.rag._resolve_llm", return_value=MagicMock()):
            response = client.post("/api/rag/query", json={
                "question": "What is RAG?",
                "collection": "test-col"
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["answer"] == "RAG answer"

def test_rag_list_collections(client):
    with patch("services.api.routes.rag.get_rag_service") as mock_service_factory:
        mock_service = MagicMock()
        mock_service.list_collections.return_value = ["col1", "col2"]
        mock_service_factory.return_value = mock_service
        
        response = client.get("/api/rag/collections")
        assert response.status_code == 200
        assert "col1" in response.get_json()["collections"]

def test_rag_delete_collection(client):
    with patch("services.api.routes.rag.get_rag_service") as mock_service_factory:
        mock_service = MagicMock()
        mock_service_factory.return_value = mock_service
        
        response = client.delete("/api/rag/collection", json={"collection": "old-col"})
        assert response.status_code == 200
        assert response.get_json()["status"] == "deleted"
        mock_service.delete_collection.assert_called_once_with("old-col")
