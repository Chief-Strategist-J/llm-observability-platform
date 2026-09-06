import pytest
from budget_provisioner.features.budget_management.service import BudgetManagementService, BudgetNotFoundError

def test_create_or_update_budget(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    config = service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    assert config.user_id == "usr-1"
    assert config.model == "gpt-4"
    assert config.max_budget == 100.0
    assert config.window_size_secs == 3600
    assert config.initial_fill_fraction == 0.2
    
    assert "budget:usr-1:gpt-4" in mock_redis.invalidated_keys
    assert len(mock_metrics.invalidations) == 1
    assert mock_metrics.invalidations[0]["user_id"] == "usr-1"

def test_get_budget(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    config = service.get_budget("usr-1", "gpt-4")
    assert config is not None
    assert config.max_budget == 100.0
    
    missing = service.get_budget("usr-1", "non-existent")
    assert missing is None

def test_list_budgets(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="claude-3",
        max_budget=200.0,
        window_size_secs=7200,
        initial_fill_fraction=0.5
    )
    
    budgets = service.list_budgets("usr-1")
    assert len(budgets) == 2
    models = {b.model for b in budgets}
    assert models == {"gpt-4", "claude-3"}

def test_delete_budget(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    mock_redis.invalidated_keys.clear()
    
    deleted = service.delete_budget("usr-1", "gpt-4")
    assert deleted is True
    assert "budget:usr-1:gpt-4" in mock_redis.invalidated_keys
    
    config = service.get_budget("usr-1", "gpt-4")
    assert config is None
    
    deleted_again = service.delete_budget("usr-1", "gpt-4")
    assert deleted_again is False

def test_get_budget_status_from_redis(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    mock_redis.status_data["budget:usr-1:gpt-4"] = {
        "tokens_remaining": "75.5",
        "burn_rate": "1.5"
    }
    
    status_info = service.get_budget_status("usr-1", "gpt-4")
    assert status_info.tokens_remaining == 75.5
    assert status_info.burn_rate == 1.5

def test_get_budget_status_defaults(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    service.create_or_update_budget(
        user_id="usr-1",
        model="gpt-4",
        max_budget=100.0,
        window_size_secs=3600,
        initial_fill_fraction=0.2
    )
    
    status_info = service.get_budget_status("usr-1", "gpt-4")
    assert status_info.tokens_remaining == 20.0
    assert status_info.burn_rate == 0.0

def test_get_budget_status_not_found(mock_db, mock_redis, mock_metrics) -> None:
    service = BudgetManagementService(
        db_port=mock_db,
        redis_port=mock_redis,
        metrics_port=mock_metrics
    )
    
    with pytest.raises(BudgetNotFoundError):
        service.get_budget_status("usr-1", "gpt-4")
