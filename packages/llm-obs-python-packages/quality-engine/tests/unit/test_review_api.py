from __future__ import annotations
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.rest.v1.app import app
from shared.types.quality_score_row import QualityScoreRow

client = TestClient(app)

def test_get_review_queue_endpoint():
    mock_repo = MagicMock()
    app.state.repo = mock_repo
    
    mock_row = QualityScoreRow(
        span_id="span_123",
        trace_id="trace_123",
        model="gpt-4",
        endpoint="/v1/chat/completions",
        prompt_type="chat",
        response_language="en",
        composite_score=0.85,
        coherence_score=0.9,
        toxicity_score=0.05,
        faithfulness_score=0.95,
        perplexity_score=1.5,
        quality_flags=["LOW_COHERENCE"],
        skipped_reason=None,
        scored_at=datetime.now(timezone.utc),
        review_status="pending",
        reviewed_at=None,
    )
    mock_repo.get_review_queue.return_value = [mock_row]

    resp = client.get("/v1/review/queue?status=pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["span_id"] == "span_123"
    assert data[0]["review_status"] == "pending"
    mock_repo.get_review_queue.assert_called_once_with("pending")

def test_submit_review_endpoint_success():
    mock_repo = MagicMock()
    app.state.repo = mock_repo
    mock_repo.update_review_status.return_value = True

    resp = client.post("/v1/review/span_123", json={"review_status": "approved"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["span_id"] == "span_123"
    assert data["review_status"] == "approved"
    assert "reviewed_at" in data
    mock_repo.update_review_status.assert_called_once()

def test_submit_review_endpoint_not_found():
    mock_repo = MagicMock()
    app.state.repo = mock_repo
    mock_repo.update_review_status.return_value = False

    resp = client.post("/v1/review/span_nonexistent", json={"review_status": "rejected"})
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]
