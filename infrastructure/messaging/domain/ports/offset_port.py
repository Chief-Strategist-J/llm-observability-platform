from abc import ABC, abstractmethod
from typing import Optional
from domain.ports.database_port import ConsumerOffset


class OffsetPort(ABC):
    @abstractmethod
    def save_consumer_offset(self, offset: ConsumerOffset) -> bool:
        pass

    @abstractmethod
    def get_consumer_offset(self, consumer_group: str, topic: str, partition: int) -> Optional[ConsumerOffset]:
        pass
