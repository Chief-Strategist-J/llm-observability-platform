from __future__ import annotations
import pytest
import random
from datetime import datetime, timezone
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from api.rest.v1.app import app
from shared.types.quality_score_row import QualityScoreRow

client = TestClient(app)

def _random_row(span_id: str) -> QualityScoreRow:
    return QualityScoreRow(
        span_id=span_id,
        trace_id=f"trace_{random.randint(1000, 9999)}",
        model=random.choice(["gpt-4o", "claude-3-5-sonnet", "llama-3"]),
        endpoint="/v1/chat/completions",
        prompt_type=random.choice(["chat", "code", "rag", "classification"]),
        response_language=random.choice(["en", "es", "fr", "de"]),
        composite_score=random.uniform(0.1, 0.99),
        coherence_score=random.uniform(0.1, 0.99),
        toxicity_score=random.uniform(0.01, 0.3),
        faithfulness_score=random.uniform(0.5, 0.99),
        perplexity_score=random.uniform(1.0, 50.0),
        quality_flags=[],
        skipped_reason=None,
        scored_at=datetime.now(timezone.utc),
        review_status="pending",
        reviewed_at=None,
    )

@pytest.mark.performance
def test_load_review_queue_retrieval():
    mock_repo = MagicMock()
    app.state.repo = mock_repo
    
    # Simulate retrieving 100 rows from the review queue
    mock_rows = [_random_row(f"span_{i}") for i in range(100)]
    mock_repo.get_review_queue.return_value = mock_rows

    for _ in range(10):  # Run 10 times to simulate concurrent requests
        resp = client.get("/v1/review/queue?status=pending")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 100
        assert data[0]["review_status"] == "pending"

@pytest.mark.performance
def test_load_review_submissions():
    mock_repo = MagicMock()
    app.state.repo = mock_repo
    mock_repo.update_review_status.return_value = True

    errors = []
    # Submit 100 reviews in sequence
    for i in range(100):
        status = random.choice(["approved", "rejected"])
        resp = client.post(f"/v1/review/span_{i}", json={"review_status": status})
        if resp.status_code != 200:
            errors.append(resp.status_code)
        else:
            data = resp.json()
            assert data["span_id"] == f"span_{i}"
            assert data["review_status"] == status

    assert not errors, f"Failed review submission: {errors}"
