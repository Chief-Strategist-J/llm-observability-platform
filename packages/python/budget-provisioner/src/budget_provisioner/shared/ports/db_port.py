from abc import ABC, abstractmethod
from typing import Optional, List
from budget_provisioner.features.budget_management.types import BudgetConfig

class DbPort(ABC):
    @abstractmethod
    def upsert_budget(
        self,
        user_id: str,
        model: str,
        max_budget: float,
        window_size_secs: int,
        initial_fill_fraction: float
    ) -> BudgetConfig:
        pass

    @abstractmethod
    def get_budget(self, user_id: str, model: str) -> Optional[BudgetConfig]:
        pass

    @abstractmethod
    def list_budgets(self, user_id: str) -> List[BudgetConfig]:
        pass

    @abstractmethod
    def delete_budget(self, user_id: str, model: str) -> bool:
        pass
