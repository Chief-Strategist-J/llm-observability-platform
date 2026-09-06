from typing import List, Optional
from budget_provisioner.shared.ports.db_port import DbPort
from budget_provisioner.features.budget_management.types import BudgetConfig

class BudgetRepository:
    def __init__(self, db_port: DbPort) -> None:
        self._db = db_port

    def save(
        self,
        user_id: str,
        model: str,
        max_budget: float,
        window_size_secs: int,
        initial_fill_fraction: float
    ) -> BudgetConfig:
        return self._db.upsert_budget(
            user_id=user_id,
            model=model,
            max_budget=max_budget,
            window_size_secs=window_size_secs,
            initial_fill_fraction=initial_fill_fraction
        )

    def find_by_user_model(self, user_id: str, model: str) -> Optional[BudgetConfig]:
        return self._db.get_budget(user_id, model)

    def find_all_by_user(self, user_id: str) -> List[BudgetConfig]:
        return self._db.list_budgets(user_id)

    def remove(self, user_id: str, model: str) -> bool:
        return self._db.delete_budget(user_id, model)
