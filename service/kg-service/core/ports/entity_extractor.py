from abc import ABC, abstractmethod
from typing import List
from core.domain.models import Entity, Relation

class EntityExtractorPort(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Entity]:
        pass
    
    @abstractmethod
    async def extract_relations(self, text: str, entities: List[Entity]) -> List[Relation]:
        pass
