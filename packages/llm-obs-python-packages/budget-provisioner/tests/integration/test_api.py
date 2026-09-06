import jwt
from fastapi import status

def get_auth_headers(secret: str) -> dict:
    token = jwt.encode({"sub": "test-service"}, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

def test_health_check(client) -> None:
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy", "service": "budget-provisioner"}

def test_unauthorized_requests(client) -> None:
    response = client.get("/budgets/usr-1")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post(
        "/budgets/usr-1/gpt-4",
        json={"max_budget": 100.0}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.delete("/budgets/usr-1/gpt-4")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.get("/budgets/usr-1/gpt-4/status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_invalid_token_requests(client) -> None:
    headers = {"Authorization": "Bearer invalid-token-value"}
    response = client.get("/budgets/usr-1", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_and_get_budget(client, test_container) -> None:
    headers = get_auth_headers(test_container.config.internal_jwt_secret)
    
    response = client.post(
        "/budgets/usr-1/gpt-4",
        headers=headers,
        json={
            "max_budget": 150.0,
            "window_size_secs": 1800,
            "initial_fill_fraction": 0.3
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["user_id"] == "usr-1"
    assert data["model"] == "gpt-4"
    assert data["max_budget"] == 150.0
    assert data["window_size_secs"] == 1800
    assert data["initial_fill_fraction"] == 0.3
    assert "created_at" in data
    assert "updated_at" in data

    response = client.post(
        "/budgets/usr-1/gpt-4",
        headers=headers,
        json={
            "max_budget": 200.0,
            "window_size_secs": 1800,
            "initial_fill_fraction": 0.3
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["max_budget"] == 200.0

    response = client.get("/budgets/usr-1", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    budgets = response.json()["budgets"]
    assert len(budgets) == 1
    assert budgets[0]["model"] == "gpt-4"
    assert budgets[0]["max_budget"] == 200.0

def test_delete_budget(client, test_container) -> None:
    headers = get_auth_headers(test_container.config.internal_jwt_secret)
    
    client.post(
        "/budgets/usr-1/gpt-4",
        headers=headers,
        json={"max_budget": 150.0}
    )
    
    response = client.delete("/budgets/usr-1/gpt-4", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"success": True, "message": "Budget deleted successfully"}

    response = client.delete("/budgets/usr-1/gpt-4", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_get_budget_status(client, test_container, mock_redis) -> None:
    headers = get_auth_headers(test_container.config.internal_jwt_secret)
    
    response = client.get("/budgets/usr-1/gpt-4/status", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    client.post(
        "/budgets/usr-1/gpt-4",
        headers=headers,
        json={
            "max_budget": 150.0,
            "initial_fill_fraction": 0.2
        }
    )
    
    response = client.get("/budgets/usr-1/gpt-4/status", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == "usr-1"
    assert data["model"] == "gpt-4"
    assert data["tokens_remaining"] == 30.0
    assert data["burn_rate"] == 0.0

    mock_redis.status_data["budget:usr-1:gpt-4"] = {
        "tokens_remaining": "95.0",
        "burn_rate": "2.4"
    }

    response = client.get("/budgets/usr-1/gpt-4/status", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["tokens_remaining"] == 95.0
    assert data["burn_rate"] == 2.4
