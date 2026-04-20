import pytest
from unittest.mock import patch, MagicMock
from services.agents.base.agent import AgentOutput

def test_run_agent_success(client):
    mock_output = AgentOutput(text="Agent result", sources=[], metadata={})
    
    with patch("services.api.routes.agents.get_rag_service") as mock_rag_factory:
        mock_rag_factory.return_value = MagicMock()
        with patch("services.orchestrator.executor.AgentExecutorService.execute", return_value=mock_output):
            response = client.post("/api/agent/run", json={
                "input": "Run task",
                "agent_type": "chat",
                "provider": "openai"
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert data["output"] == "Agent result"
            assert data["agent_type"] == "chat"

def test_list_agents(client):
    response = client.get("/api/agent/list")
    assert response.status_code == 200
    data = response.get_json()
    assert "chat" in data["agents"]
    assert "rag" in data["agents"]

def test_agent_types(client):
    response = client.get("/api/agent/types")
    assert response.status_code == 200
    data = response.get_json()
    assert "chat" in data["agents"]
    assert "openai" in data["providers"]
