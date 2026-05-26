from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.rest.v1.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@patch("api.rest.v1.app.trigger_ewma_workflow", new_callable=AsyncMock)
def test_trigger(mock_trigger: AsyncMock) -> None:
    mock_trigger.return_value = {
        "status": "triggered",
        "workflow_id": "test-id",
        "run_id": "run-id",
    }

    response = client.post("/trigger", json={"force_hour": 42})
    assert response.status_code == 200
    assert response.json()["status"] == "triggered"
    mock_trigger.assert_awaited_once_with(force_hour=42)
