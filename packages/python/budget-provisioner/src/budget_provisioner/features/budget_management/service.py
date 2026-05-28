from typing import List, Optional
from opentelemetry import trace
from budget_provisioner.shared.ports.db_port import DbPort
from budget_provisioner.shared.ports.redis_port import RedisPort
from budget_provisioner.shared.ports.metrics_port import MetricsPort
from budget_provisioner.features.budget_management.types import BudgetConfig, BudgetStatus

tracer = trace.get_tracer("budget-provisioner")

class BudgetNotFoundError(Exception):
    pass

class BudgetManagementService:
    def __init__(
        self,
        db_port: DbPort,
        redis_port: RedisPort,
        metrics_port: MetricsPort
    ) -> None:
        self._db = db_port
        self._redis = redis_port
        self._metrics = metrics_port

    def create_or_update_budget(
        self,
        user_id: str,
        model: str,
        max_budget: float,
        window_size_secs: int,
        initial_fill_fraction: float
    ) -> BudgetConfig:
        with tracer.start_as_current_span(
            "budget_service.create_or_update_budget",
            attributes={
                "budget.user_id": user_id,
                "budget.model": model,
                "budget.max_budget": max_budget,
                "budget.window_size_secs": window_size_secs,
                "budget.initial_fill_fraction": initial_fill_fraction
            }
        ) as span:
            try:
                config = self._db.upsert_budget(
                    user_id=user_id,
                    model=model,
                    max_budget=max_budget,
                    window_size_secs=window_size_secs,
                    initial_fill_fraction=initial_fill_fraction
                )
                self._redis.invalidate_budget_cache(user_id, model)
                self._metrics.record_invalidation(user_id, model)
                return config
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def get_budget(self, user_id: str, model: str) -> Optional[BudgetConfig]:
        with tracer.start_as_current_span(
            "budget_service.get_budget",
            attributes={
                "budget.user_id": user_id,
                "budget.model": model
            }
        ) as span:
            try:
                return self._db.get_budget(user_id, model)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def list_budgets(self, user_id: str) -> List[BudgetConfig]:
        with tracer.start_as_current_span(
            "budget_service.list_budgets",
            attributes={
                "budget.user_id": user_id
            }
        ) as span:
            try:
                return self._db.list_budgets(user_id)
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def delete_budget(self, user_id: str, model: str) -> bool:
        with tracer.start_as_current_span(
            "budget_service.delete_budget",
            attributes={
                "budget.user_id": user_id,
                "budget.model": model
            }
        ) as span:
            try:
                deleted = self._db.delete_budget(user_id, model)
                if deleted:
                    self._redis.invalidate_budget_cache(user_id, model)
                    self._metrics.record_invalidation(user_id, model)
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise

    def get_budget_status(self, user_id: str, model: str) -> BudgetStatus:
        with tracer.start_as_current_span(
            "budget_service.get_budget_status",
            attributes={
                "budget.user_id": user_id,
                "budget.model": model
            }
        ) as span:
            try:
                config = self._db.get_budget(user_id, model)
                if not config:
                    raise BudgetNotFoundError("Budget config not found")
                
                status_data = self._redis.get_token_bucket_status(user_id, model)
                if status_data:
                    return BudgetStatus(
                        user_id=user_id,
                        model=model,
                        tokens_remaining=float(status_data.get("tokens_remaining", 0.0)),
                        burn_rate=float(status_data.get("burn_rate", 0.0))
                    )
                
                return BudgetStatus(
                    user_id=user_id,
                    model=model,
                    tokens_remaining=config.max_budget * config.initial_fill_fraction,
                    burn_rate=0.0
                )
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
                raise
