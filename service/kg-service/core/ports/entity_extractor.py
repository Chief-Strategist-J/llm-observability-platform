from abc import ABC, abstractmethod

from core.domain.models import Entity, Relation


class EntityExtractorPort(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list[Entity]:
        pass

    @abstractmethod
    async def extract_relations(
        self, text: str, entities: list[Entity]
    ) -> list[Relation]:
        pass
