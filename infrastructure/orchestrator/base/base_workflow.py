from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from abc import ABC, abstractmethod

class BaseWorkflow(ABC):
    @abstractmethod
    async def run(self, service_name: str) -> str:
        pass
