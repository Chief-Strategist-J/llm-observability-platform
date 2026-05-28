import pytest
from datetime import datetime, timezone
from typing import Optional, List
from fastapi.testclient import TestClient

from budget_provisioner.shared.ports.db_port import DbPort
from budget_provisioner.shared.ports.redis_port import RedisPort
from budget_provisioner.shared.ports.metrics_port import MetricsPort
from budget_provisioner.features.budget_management.types import BudgetConfig
from budget_provisioner.shared.di.container import Container
from budget_provisioner.config import Config
from budget_provisioner.api.main import create_app

class MockDbPort(DbPort):
    def __init__(self) -> None:
        self.budgets: dict[str, BudgetConfig] = {}

    def upsert_budget(
        self,
        user_id: str,
        model: str,
        max_budget: float,
        window_size_secs: int,
        initial_fill_fraction: float
    ) -> BudgetConfig:
        key = f"{user_id}:{model}"
        now = datetime.now(timezone.utc)
        created_at = now
        if key in self.budgets:
            created_at = self.budgets[key].created_at
        
        config = BudgetConfig(
            user_id=user_id,
            model=model,
            max_budget=max_budget,
            window_size_secs=window_size_secs,
            initial_fill_fraction=initial_fill_fraction,
            created_at=created_at,
            updated_at=now
        )
        self.budgets[key] = config
        return config

    def get_budget(self, user_id: str, model: str) -> Optional[BudgetConfig]:
        return self.budgets.get(f"{user_id}:{model}")

    def list_budgets(self, user_id: str) -> List[BudgetConfig]:
        return [b for b in self.budgets.values() if b.user_id == user_id]

    def delete_budget(self, user_id: str, model: str) -> bool:
        key = f"{user_id}:{model}"
        if key in self.budgets:
            del self.budgets[key]
            return True
        return False

class MockRedisPort(RedisPort):
    def __init__(self) -> None:
        self.invalidated_keys: List[str] = []
        self.status_data: dict[str, dict] = {}

    def invalidate_budget_cache(self, user_id: str, model: str) -> None:
        self.invalidated_keys.append(f"budget:{user_id}:{model}")

    def get_token_bucket_status(self, user_id: str, model: str) -> Optional[dict]:
        return self.status_data.get(f"budget:{user_id}:{model}")

class MockMetricsPort(MetricsPort):
    def __init__(self) -> None:
        self.requests: List[dict] = []
        self.invalidations: List[dict] = []

    def record_request(self, method: str, path: str, status_code: int) -> None:
        self.requests.append({"method": method, "path": path, "status_code": status_code})

    def record_invalidation(self, user_id: str, model: str) -> None:
        self.invalidations.append({"user_id": user_id, "model": model})

@pytest.fixture
def mock_db() -> MockDbPort:
    return MockDbPort()

@pytest.fixture
def mock_redis() -> MockRedisPort:
    return MockRedisPort()

@pytest.fixture
def mock_metrics() -> MockMetricsPort:
    return MockMetricsPort()

@pytest.fixture
def test_container(mock_db, mock_redis, mock_metrics) -> Container:
    config = Config(
        postgres_dsn="postgresql://postgres:postgres@localhost:5432/test",
        redis_url="redis://localhost:6379/0",
        internal_jwt_secret="test-secret-key",
        host="127.0.0.1",
        port=8001
    )
    container = Container(config=config)
    container.postgres_adapter = mock_db
    container.redis_adapter = mock_redis
    container.metrics_adapter = mock_metrics
    container.budget_service._db = mock_db
    container.budget_service._redis = mock_redis
    container.budget_service._metrics = mock_metrics
    return container

@pytest.fixture
def client(test_container) -> TestClient:
    app = create_app(container=test_container)
    return TestClient(app)
